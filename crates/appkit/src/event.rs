use foundation::geometry::NSPoint;
use objc::object::Id;
use std::collections::VecDeque;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, Instant};

use crate::nsevent::{self, Fields, kind};
use crate::window;

const MOUSE_LOOK_DELTA_SCALE: f32 = 0.003;

fn mouse_look_delta_scale(buttons: u32, associated: bool) -> f32 {
    let right_button = sdl3::mouse::mask(sdl3::mouse::RIGHT);
    if !associated || buttons & right_button != 0 {
        MOUSE_LOOK_DELTA_SCALE
    } else {
        1.0
    }
}

/// Drain SDL's queue once, delivering what this tree can deliver.
///
/// `app` is the application, which is the object a window notification is posted
/// about when the event names no window this crate made.
pub fn pump(app: Id) {
    let _ = app;
    // Before anything else: a thread waiting for a GL context this one holds is
    // a thread that is not drawing, and reaching here is what says this one has
    // finished with it. See `opengl::release_for_other_threads`.
    crate::opengl::release_for_other_threads();
    gamecontroller::pump();
    debug_resize();
    debug_key();
    crate::script::run();
    trace_views();
    while let Some(event) = sdl3::video::poll() {
        deliver(event);
    }
    // Copied out first: a guard in the loop's head would be held across every
    // hook, and a hook that runs guest code can turn this pump again.
    let hooks = PUMP_HOOKS.lock().unwrap_or_else(|e| e.into_inner()).clone();
    for hook in hooks {
        hook();
    }
    crate::application::check_last_window_closed();
    crate::backing::pump();
}

static PUMP_HOOKS: std::sync::Mutex<Vec<fn()>> = std::sync::Mutex::new(Vec::new());

/// Run `hook` on every turn of the main thread's event pump, after input is
/// delivered and before stores are presented.
///
/// For another toolkit whose own main loop has to turn on this thread: WebKit's
/// GTK main context is serviced here, so its callbacks reach the guest on the
/// thread AppKit promises them on.
pub fn add_pump_hook(hook: fn()) {
    let mut hooks = PUMP_HOOKS.lock().unwrap_or_else(|e| e.into_inner());
    if !hooks
        .iter()
        .any(|existing| std::ptr::fn_addr_eq(*existing, hook))
    {
        hooks.push(hook);
    }
}

/// `ROSEMARY_DEBUG_RESIZE=WxH@SECONDS`: resize the program's window once, that
/// many seconds in.
///
/// A resize is the one window event that cannot be produced without a person
/// dragging a corner, which makes "does the program follow its window" the one
/// thing about a window that is untestable from a script. `SDL_SetWindowSize`
/// on a resizable window raises the same `SDL_EVENT_WINDOW_RESIZED` the
/// compositor would, so everything downstream of the pump - the content view's
/// frame, the subviews, the delegate's `-windowDidResize:` - is exercised for
/// real.
fn debug_resize() {
    use std::sync::OnceLock;
    use std::time::Instant;

    static REQUEST: OnceLock<Option<(i32, i32, f64)>> = OnceLock::new();
    static START: OnceLock<Instant> = OnceLock::new();
    static DONE: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);

    let request = *REQUEST.get_or_init(|| {
        let value = std::env::var("ROSEMARY_DEBUG_RESIZE").ok()?;
        let (size, after) = value.split_once('@').unwrap_or((value.as_str(), "5"));
        let (width, height) = size.split_once('x')?;
        Some((
            width.trim().parse().ok()?,
            height.trim().parse().ok()?,
            after.trim().parse().unwrap_or(5.0),
        ))
    });
    let Some((width, height, after)) = request else {
        return;
    };
    if DONE.load(std::sync::atomic::Ordering::Relaxed)
        || START.get_or_init(Instant::now).elapsed().as_secs_f64() < after
    {
        return;
    }
    DONE.store(true, std::sync::atomic::Ordering::Relaxed);
    let Some(sdl) = window::sdl_windows().into_iter().next() else {
        return;
    };
    eprintln!("rosemary: appkit: ROSEMARY_DEBUG_RESIZE: resizing to {width}x{height}");
    sdl3::video::set_window_size(sdl, width, height);
}

/// `ROSEMARY_DEBUG_KEY=NAME[,NAME...]@SECONDS`: press and release each key in
/// turn, that many seconds in.
///
/// The companion to `ROSEMARY_DEBUG_RESIZE`, and there for the same reason: a
/// keystroke cannot be produced from a script under a compositor that does not
/// implement the virtual-keyboard protocol, so "does the program answer the
/// keyboard" is otherwise only testable by hand. The event goes through
/// [`deliver`], so the keymap, `-keyDown:` and the responder chain are exercised
/// exactly as a real press would exercise them.
fn debug_key() {
    use std::sync::OnceLock;
    use std::time::Instant;

    static REQUEST: OnceLock<Option<(Vec<u32>, f64)>> = OnceLock::new();
    static START: OnceLock<Instant> = OnceLock::new();
    static DONE: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);

    let request = REQUEST.get_or_init(|| {
        let value = std::env::var("ROSEMARY_DEBUG_KEY").ok()?;
        let (names, after) = value.split_once('@').unwrap_or((value.as_str(), "5"));
        let keys: Vec<u32> = names
            .split(',')
            .filter_map(|n| scancode(n.trim()))
            .collect();
        match keys.is_empty() {
            true => None,
            false => Some((keys, after.trim().parse().unwrap_or(5.0))),
        }
    });
    let Some((keys, after)) = request else {
        return;
    };
    let after = *after;
    if DONE.load(std::sync::atomic::Ordering::Relaxed)
        || START.get_or_init(Instant::now).elapsed().as_secs_f64() < after
    {
        return;
    }
    DONE.store(true, std::sync::atomic::Ordering::Relaxed);
    let Some(window) = window::sdl_windows()
        .into_iter()
        .map(sdl3::video::window_id)
        .next()
    else {
        return;
    };
    eprintln!("rosemary: appkit: ROSEMARY_DEBUG_KEY: pressing scancodes {keys:?}");
    for scancode in keys {
        for down in [true, false] {
            deliver(sdl3::video::Event::Key {
                window,
                scancode: *scancode,
                key: 0,
                modifiers: 0,
                down,
                repeat: false,
            });
        }
    }
}

/// The USB HID usage id `ROSEMARY_DEBUG_KEY`'s value names, or a raw number.
pub(crate) fn scancode(name: &str) -> Option<u32> {
    use sdl3::keycodes::scancode;
    Some(match name.to_ascii_lowercase().as_str() {
        "return" | "enter" => scancode::RETURN,
        "escape" => scancode::ESCAPE,
        "tab" => scancode::TAB,
        "space" => scancode::SPACE,
        "right" => scancode::RIGHT,
        "left" => scancode::LEFT,
        "down" => scancode::DOWN,
        "up" => scancode::UP,
        other => other.parse().ok()?,
    })
}

/// `ROSEMARY_TRACE_VIEWS=SECONDS`: print each window and the tree of views under
/// it, once, that many seconds in.
///
/// Companion to `ROSEMARY_DEBUG_RESIZE`, and needed for the same reason: the
/// question a resize raises is which view ended up the wrong size, and the view
/// that matters is one the *guest* made - so it is in no debugger's symbol
/// table, and a release build has inlined every accessor that would name it.
/// Printed after the window's own size so the two can be compared on sight.
fn trace_views() {
    use std::sync::OnceLock;
    use std::time::Instant;

    static AFTER: OnceLock<Option<f64>> = OnceLock::new();
    static START: OnceLock<Instant> = OnceLock::new();
    static DONE: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);

    let Some(after) = *AFTER.get_or_init(|| {
        std::env::var("ROSEMARY_TRACE_VIEWS")
            .ok()
            .map(|value| value.trim().parse().unwrap_or(5.0))
    }) else {
        return;
    };
    if DONE.load(std::sync::atomic::Ordering::Relaxed)
        || START.get_or_init(Instant::now).elapsed().as_secs_f64() < after
    {
        return;
    }
    DONE.store(true, std::sync::atomic::Ordering::Relaxed);

    let mut out = String::new();
    for object in window::all() {
        // SAFETY: a window this crate made.
        let sdl = unsafe { window::sdl_window(object) };
        let title = sdl3::video::window_title(sdl)
            .to_string_lossy()
            .into_owned();
        let position = window::global_position(sdl);
        let size = sdl3::video::window_size(sdl);
        let id = sdl3::video::window_id(sdl);
        let flags = sdl3::video::window_flags(sdl);
        out.push_str(&format!(
            "rosemary: appkit: window {object:p} id={id} title={title:?} shown={} position={position:?} size={size:?} flags={flags:#x}\n",
            window::is_shown(object),
        ));
        // SAFETY: null or a view this runtime allocated.
        unsafe { crate::view::describe(window::content_view_of(object), 1, &mut out) };
    }
    eprint!("{out}");
}

pub(crate) fn deliver(event: sdl3::video::Event) {
    if !crate::dialog::deliver_modal(&event) {
        deliver_past_modal(event);
    }
}

/// [`deliver`] for the modal dialog's own loop, which has already had its
/// turn at `event`: queueing it for the dialog again would hand it straight
/// back, and the loop would never wait for input again.
pub(crate) fn deliver_past_modal(event: sdl3::video::Event) {
    use sdl3::video::Event;
    if crate::dialog::deliver(&event) {
        return;
    }
    match event {
        // A quit is the whole application, and is the one event that is not
        // about a window: it is what a program's `-applicationShouldTerminate:`
        // would be asked about, and until there is one it ends the run loop the
        // way `-terminate:` does.
        Event::Quit => {
            let app = crate::application::shared();
            if !app.is_null() {
                // SAFETY: `-terminate:` is `void (id, SEL, id)` on the shared
                // application, which this crate installed.
                unsafe {
                    let f: unsafe extern "C" fn(Id, objc::sel::Sel, Id) =
                        std::mem::transmute(objc::msg::entry());
                    f(app, objc::sel::get("terminate:"), std::ptr::null_mut());
                }
            }
        }
        // The compositor's close button, or its shortcut, which is what the
        // title bar's close button is on a Mac: `-performClose:`, so the
        // delegate may refuse and `-close` does the rest.
        Event::WindowClosed { window } => {
            let _trace_scope = InputTraceScope::begin();
            input_trace(&format!("stage=window_closed window_id={window}"));
            if crate::decor::window_closed(window) {
                return;
            }
            let object = object_for(window);
            if !object.is_null() {
                // SAFETY: `-performClose:` is `void (id, SEL, id)` on a window
                // this crate made.
                unsafe {
                    let f: unsafe extern "C" fn(Id, objc::sel::Sel, Id) =
                        std::mem::transmute(objc::msg::entry());
                    f(object, objc::sel::get("performClose:"), object);
                }
            }
        }
        Event::WindowHitTest { window } => crate::decor::hit_test_pressed(window),
        Event::WindowState { window } => {
            let object = object_for(window);
            if !object.is_null()
                && let Some(name) = window::window_state_changed(object)
            {
                post(window, name);
            }
        }
        // A program that keeps its own copy of where its window is - a Win32
        // layer mapping client rectangles to the desktop does - learns of a move
        // from this alone. A Wayland toplevel does not move in the desktop
        // this runtime reports (see `window::global_position`), because a
        // program that only listens for the moves it makes itself would keep
        // mapping the pointer against the origin it asked for.
        Event::WindowMoved { window } => post(window, window::DID_MOVE),
        Event::WindowDisplayChanged { window } => post(window, window::DID_CHANGE_SCREEN),
        Event::WindowResized { window, .. } => {
            // The content view follows the window, as it does on
            // `-setContentView:` and for the same reason: a view that kept its
            // old size after a resize would draw into part of the window and
            // report a backing store the window does not have.
            let object = object_for(window);
            let content = window::content_view_of(object);
            if !object.is_null() {
                window::size_settled(object);
                window::fit_content_view(object);
                crate::screen::confine_pointer(object);
            }
            // A resized view's tracking rectangle is the wrong shape, and
            // AppKit asks for a new one here rather than resizing the old.
            // SAFETY: null or a view this crate made.
            unsafe { crate::view::update_tracking_areas(content) };
            // Cursor rectangles are in their view's coordinates too. A
            // reset lets a view rebuild rectangles derived from its old bounds
            // before the next cursor hit test chooses the wrong cursor.
            // SAFETY: null or the content view of a window this crate made.
            unsafe { crate::cursor::reset_rects_in_tree(content) };
            post(window, window::DID_RESIZE);
        }
        // The frame remains in points when a window crosses onto a display at
        // another scale, but its backing store does not. AppKit tells guests to
        // recompute pixel-sized viewports with this notification.
        Event::WindowBackingChanged { window } => {
            post(window, window::DID_CHANGE_BACKING_PROPERTIES);
        }
        Event::WindowMouse { window, entered } => {
            // A disassociated pointer never leaves: its cursor is frozen where
            // it was, and SDL's integrated position reaching a window edge is
            // not the guest's pointer going anywhere. A guest told it left
            // (Unity does) gives the lock up.
            if !entered && !crate::screen::mouse_is_associated() {
                return;
            }
            if !entered {
                crate::decor::pointer_left(window);
            }
            // A menu's popup is chrome from its first pixel; anything else
            // is decided by the moves that follow.
            if entered {
                crate::cursor::set_over_chrome(crate::decor::is_chrome_popup(window));
            }
            // A resize is performed from outside the client area. SDL reports
            // the resulting leave and re-entry as window events rather than
            // mouse-motion events; dropping them leaves an NSTrackingArea
            // owner believing the pointer is outside forever.
            if entered && let Some((x, y, _)) = sdl3::video::mouse_state() {
                track_pointer(window, x, y);
            }
            crate::cursor::apply();
            match entered {
                true => crate::cursor::update_tracking(object_for(window), false),
                false => crate::cursor::forget_tracking(object_for(window)),
            }
        }
        Event::WindowFocus { window, gained } => {
            let _trace_scope = InputTraceScope::begin();
            input_trace(&format!(
                "stage=window_focus window_id={window} gained={gained}"
            ));
            crate::decor::focus_changed(window, gained);
            let object = object_for(window);
            if !object.is_null() && gained {
                window::set_key_window(object);
                // SDL drops relative mouse mode when focus goes, and a window
                // made while the guest was disassociated never entered it.
                crate::screen::apply_mouse_association();
                crate::screen::confine_pointer(object);
            }
            post(
                window,
                match gained {
                    true => window::DID_BECOME_KEY,
                    false => window::DID_RESIGN_KEY,
                },
            );
        }
        Event::Key {
            window: id,
            scancode,
            key,
            modifiers,
            down,
            repeat,
        } => {
            let _trace_scope = InputTraceScope::begin();
            input_trace(&format!(
                "stage=sdl_key window_id={id} scancode={scancode} key_sym={key:#x} down={down} repeat={repeat} modifiers={modifiers:#x}"
            ));
            if crate::decor::key(scancode, down) {
                input_trace(&format!(
                    "stage=key_decoration_consumed window_id={id} scancode={scancode} down={down}"
                ));
                return;
            }
            let text = crate::keymap::characters(
                scancode,
                crate::keymap::typed_key(scancode, key, modifiers),
            );
            let modifiers = crate::keymap::modifiers(modifiers);
            let code = crate::keymap::virtual_key(scancode);
            if down && !crate::keymap::is_modifier(scancode) {
                let window = object_for(id);
                crate::text::begin_key_interpretation(responder_of(window));
            }
            let fields = |window| Fields {
                kind: match down {
                    true => kind::KEY_DOWN,
                    false => kind::KEY_UP,
                },
                modifiers,
                key_code: code,
                characters: objc::arc::autorelease(foundation::string::from_str(&text)),
                repeat,
                window,
                ..Fields::default()
            };
            // A key equivalent is the menu's, offered before the key reaches
            // the first responder, as `-[NSApplication sendEvent:]` does.
            let equivalent_handled = down
                && !crate::keymap::is_modifier(scancode)
                && key_equivalent(object_for(id), fields(object_for(id)), &text);
            input_trace(&format!(
                "stage=key_equivalent window_id={id} scancode={scancode} virtual_key={code} down={down} repeat={repeat} text_length={} handled={equivalent_handled}",
                text.len(),
            ));
            if equivalent_handled {
                return;
            }
            // A modifier is `-flagsChanged:`, not a key down: AppKit has no
            // key-up for one, and a guest that treated it as a key would see
            // shift as a character.
            match crate::keymap::is_modifier(scancode) {
                true => send(id, None, |w, _| Fields {
                    kind: kind::FLAGS_CHANGED,
                    ..fields(w)
                }),
                false => send(id, None, |w, _| fields(w)),
            }
        }
        // A key event describes a physical key. Text input is the separate,
        // layout- and IME-resolved commit, and must go to the focused
        // `NSTextInputClient`; `-characters` is not a substitute for it.
        Event::Text { window, text } => {
            let window = object_for(window);
            let responder = responder_of(window);
            if crate::text::accepts_host_text(responder) {
                crate::text::commit(responder, &text);
            }
        }
        Event::TextEditing {
            window,
            text,
            start,
            length,
        } => {
            let window = object_for(window);
            let responder = responder_of(window);
            if crate::text::accepts_host_text(responder) {
                crate::text::compose(responder, &text, start, length);
            }
        }
        Event::MouseMotion {
            window: id,
            x,
            y,
            dx,
            dy,
            buttons,
        } => {
            crate::cursor::mouse_moved();
            let associated = crate::screen::mouse_is_associated();
            let _trace_scope = (buttons != 0 || !associated).then(InputTraceScope::begin);
            let expected_echo = pending_warp_target();
            let (dx, dy, warp_echo, adjusted_echo) = match take_warp_echo(x, y, dx, dy) {
                WarpEchoResult::None => (dx, dy, false, None),
                WarpEchoResult::Consumed { target } => (dx, dy, true, Some((target, None))),
                WarpEchoResult::Adjusted { target, delta } => {
                    (delta.0, delta.1, false, Some((target, Some(delta))))
                }
            };
            if buttons != 0 || !associated || warp_echo || adjusted_echo.is_some() {
                input_trace(&format!(
                    "stage=warp_echo_check window_id={id} expected={expected_echo:?} event=({x:.3},{y:.3}) consumed={warp_echo} adjusted={adjusted_echo:?}"
                ));
            }
            if warp_echo {
                return;
            }
            let delta_scale = mouse_look_delta_scale(buttons, associated);
            let (camera_dx, camera_dy) = (dx * delta_scale, dy * delta_scale);
            if buttons != 0 || !associated {
                let previous = pointer_position();
                let relative = crate::window::sdl_windows()
                    .into_iter()
                    .find(|window| sdl3::video::window_id(*window) == id)
                    .is_some_and(sdl3::video::relative_mouse_mode);
                debug_log(&format!(
                    "mouse motion id {id} raw ({x:.2},{y:.2}) delta ({dx:.2},{dy:.2}) buttons {buttons:#x} associated {associated} relative {relative} pointer ({:.2},{:.2})",
                    previous.0, previous.1,
                ));
                input_trace(&format!(
                    "stage=sdl_motion window_id={id} raw=({x:.3},{y:.3}) delta=({dx:.3},{dy:.3}) camera_delta=({camera_dx:.3},{camera_dy:.3}) scale={delta_scale:.2} buttons={buttons:#x} associated={associated} relative={relative} pointer_before=({:.3},{:.3})",
                    previous.0, previous.1,
                ));
            }
            crate::cgevent::note_mouse_delta(camera_dx, camera_dy);
            crate::screen::hold_at_edge(id, x, y, dx, dy);
            // Update the coordinate frame before a window drag reads the global
            // pointer: on Wayland SDL reports the pointer relative to this event's
            // window, which may differ from the one that sent the last event.
            let (x, y) = track_pointer(id, x, y);
            if buttons != 0 || !associated {
                input_trace(&format!(
                    "stage=sdl_motion_mapped window_id={id} location_delivered=({x:.3},{y:.3}) frozen_pointer={:?} buttons={buttons:#x} associated={}",
                    pointer_position(),
                    crate::screen::mouse_is_associated(),
                ));
            }
            // SDL's position keeps integrating the deltas of a disassociated
            // pointer, so it wanders over the chrome while the cursor the
            // program sees sits still. The chrome is for a pointer that moves.
            let on_chrome = match crate::screen::mouse_is_associated() {
                true => crate::decor::pointer_moved(id, x, y),
                false => false,
            };
            crate::cursor::set_over_chrome(on_chrome);
            // A window being dragged by `-performWindowDragWithEvent:` consumes
            // the move: it moved the window, and AppKit does not also report it
            // as a drag inside the window it just moved. Do this before returning
            // for chrome, because the drag can carry the pointer across it.
            if crate::window::drag_moved() {
                return;
            }
            if on_chrome {
                return;
            }
            let held = crate::button::held(buttons);
            // A disassociated pointer reports the deltas and none of the
            // movement: the location a guest reads back is where the cursor was
            // when it broke the link, which is what CoreGraphics does and what
            // SDL, still tracking a position inside the window, does not.
            // Before the drop below: a cursor rectangle applies whether or not
            // anything asked for `-mouseMoved:`, and AppKit re-decides the
            // pointer on every move rather than only when a rectangle changes.
            crate::cursor::apply();
            crate::cursor::update_tracking(object_for(id), held.is_some());
            let fields = |window, location, area| Fields {
                kind: crate::button::dragged_kind(held),
                modifiers: current_modifiers(),
                location,
                delta: NSPoint {
                    x: camera_dx as f64,
                    y: camera_dy as f64,
                },
                button: held.map_or(0, crate::button::number),
                window,
                tracking_area: area,
                ..Fields::default()
            };
            if held.is_none() {
                // An area made with `NSTrackingMouseMoved` has its owner sent
                // the move, and that is the whole of the delivery: the view
                // under the pointer is not sent it a second time.
                let window = object_for(id);
                let areas = crate::cursor::mouse_moved_areas(window);
                if !areas.is_empty() {
                    let location = location(window, x as f64, y as f64);
                    for area in &areas {
                        dispatch(window, nsevent::make(fields(window, location, *area)));
                    }
                    areas.into_iter().for_each(objc::arc::release);
                    return;
                }
            }
            if held.is_none() && !wants_mouse_moved(object_for(id)) {
                if tracing() {
                    eprintln!(
                        "rosemary: appkit: -mouseMoved: dropped: the window did not ask for it \
                         and no view is tracking"
                    );
                }
                return;
            }
            send(id, Some((x, y)), |window, location| {
                fields(window, location, std::ptr::null_mut())
            });
        }
        Event::MouseButton {
            window: id,
            button,
            down,
            clicks,
            x,
            y,
        } => {
            let _trace_scope = InputTraceScope::begin();
            // End the drag even when the decoration consumes this button event.
            if !down {
                crate::window::end_drag();
            }
            let associated = crate::screen::mouse_is_associated();
            let relative = crate::window::sdl_windows()
                .into_iter()
                .find(|window| sdl3::video::window_id(*window) == id)
                .is_some_and(sdl3::video::relative_mouse_mode);
            let previous = pointer_position();
            debug_log(&format!(
                "mouse button id {id} button {button} down {down} clicks {clicks} raw ({x:.2},{y:.2}) associated {associated} relative {relative} pointer ({:.2},{:.2})",
                previous.0, previous.1,
            ));
            input_trace(&format!(
                "stage=sdl_button window_id={id} button={button} down={down} clicks={clicks} raw=({x:.3},{y:.3}) associated={associated} relative={relative} pointer_before=({:.3},{:.3})",
                previous.0, previous.1,
            ));
            // The point the guest sees: a disassociated pointer's click lands
            // where its cursor froze, not where SDL's integrated position is.
            let (cx, cy) = track_pointer(id, x, y);
            input_trace(&format!(
                "stage=sdl_button_mapped window_id={id} raw=({x:.3},{y:.3}) mapped=({cx:.3},{cy:.3}) associated={}",
                crate::screen::mouse_is_associated(),
            ));
            if crate::decor::pointer_button(id, button, down, clicks, cx, cy) {
                return;
            }
            let kind = crate::button::event_kind(button, down);
            let (x, y) = track_pointer(id, x, y);
            send(id, Some((x, y)), |window, location| Fields {
                kind,
                modifiers: current_modifiers(),
                location,
                button: crate::button::number(button),
                clicks: i64::from(clicks),
                window,
                ..Fields::default()
            });
        }
        // A wheel event carries no position, so it goes to the view the pointer
        // was last over - which is where the wheel turned.
        Event::MouseWheel { window: id, x, y } => {
            let at = *POINTER.lock().unwrap_or_else(|e| e.into_inner());
            send(id, Some(at), |window, location| Fields {
                kind: kind::SCROLL_WHEEL,
                modifiers: current_modifiers(),
                location,
                delta: NSPoint {
                    x: x as f64,
                    y: y as f64,
                },
                window,
                ..Fields::default()
            });
        }
        Event::Other(_) => {}
    }
}

/// Tell a window's guest where the window actually is and how large it actually
/// is, by posting the pair of notifications a real move and resize would.
///
/// On a Mac a window is placed and sized exactly as the program asked, so the
/// program never has to look again. A Wayland compositor places a toplevel
/// itself and may hand back a different size, and a toolkit that never hears
/// about it keeps mapping pointer positions against a window that is elsewhere.
/// The same pair is what a toolkit waits for before it treats a window as
/// on-screen at all.
pub fn window_geometry_changed(object: Id) {
    // SAFETY: a window this crate made.
    let sdl = unsafe { window::sdl_window(object) };
    if sdl.is_null() {
        return;
    }
    let id = sdl3::video::window_id(sdl);
    // Only when the compositor actually chose a different size. `-windowDidResize:`
    // is not a notification a program merely notes: Unreal rebuilds its viewport
    // from it, which means dropping the GL context on the thread that draws and
    // taking it on the thread that runs this - and a context handed back and
    // forth is the one thing the GL under this runtime cannot do. A window that
    // came back the size it asked for has nothing to say.
    if let Some((width, height)) = sdl3::video::window_size(sdl)
        && window::requested_size(object) != Some((width, height))
    {
        deliver(sdl3::video::Event::WindowResized {
            window: id,
            width,
            height,
        });
    }
    post(id, window::DID_MOVE);
}

fn current_modifiers() -> u64 {
    crate::keymap::modifiers(sdl3::video::keyboard_modifiers())
}

/// Offer a key press to whatever takes it as a key equivalent: the window's
/// views, then the main menu. True when something did.
///
/// With [`crate::decor::Config::control_shortcuts`], Control also reaches a
/// menu item whose equivalent is Command, once nothing took it as it was.
fn key_equivalent(window: Id, fields: Fields, text: &str) -> bool {
    use crate::keymap::flags;
    let modifiers = fields.modifiers;
    let function_key = text
        .chars()
        .next()
        .is_some_and(|c| ('\u{F700}'..='\u{F8FF}').contains(&c));
    if modifiers & (flags::COMMAND | flags::CONTROL) == 0 && !function_key {
        return false;
    }
    let sel = objc::sel::get("performKeyEquivalent:");
    let offer = |receiver: Id, event: Id| {
        if receiver.is_null() {
            return false;
        }
        // SAFETY: `-performKeyEquivalent:` is `BOOL (id, SEL, NSEvent *)` on
        // windows and menus, both of which this crate installs it on.
        unsafe {
            let f: unsafe extern "C" fn(Id, objc::sel::Sel, Id) -> u8 =
                std::mem::transmute(objc::msg::entry());
            f(receiver, sel, event) != 0
        }
    };
    let menu = crate::menu::main_menu();
    let event = nsevent::make(fields.clone());
    if offer(window, event) || offer(menu, event) {
        return true;
    }
    let control_only = modifiers & flags::CONTROL != 0 && modifiers & flags::COMMAND == 0;
    if !(control_only && !crate::decor::config().control_shortcuts) {
        return false;
    }
    let aliased = nsevent::make(Fields {
        modifiers: (modifiers & !flags::CONTROL) | flags::COMMAND,
        ..fields
    });
    offer(menu, aliased)
}

/// A pointer position SDL reports against the window's top-left, in the
/// bottom-left frame `-locationInWindow` promises.
///
/// The base coordinate system is the whole frame, so a titlebar this runtime
/// draws is above the content view's top.
pub(crate) fn location(window: Id, x: f64, y: f64) -> NSPoint {
    let content = window::content_view_of(window);
    let height = match content.is_null() {
        true => 0.0,
        // SAFETY: `-bounds` is `NSRect (id, SEL)` on a view this crate made.
        // `NSRect` returns through a buffer, so this is the `_stret` entry:
        // through the other one the receiver would be the return slot.
        false => unsafe {
            let f: unsafe extern "C" fn(Id, objc::sel::Sel) -> foundation::geometry::NSRect =
                std::mem::transmute(objc::msg::entry_stret());
            f(content, objc::sel::get("bounds")).size.height
        },
    };
    let height = height + window::content_inset(window);
    crate::geometry::point_in_window(x, y, height)
}

/// Hand one input event to its window, as `-[NSApplication sendEvent:]` does.
fn send(id: u32, at: Option<(f32, f32)>, fields: impl FnOnce(Id, NSPoint) -> Fields) {
    let window = object_for(id);
    if window.is_null() {
        return;
    }
    let point = at
        .map(|(x, y)| location(window, x as f64, y as f64))
        .unwrap_or_default();
    dispatch(window, nsevent::make(fields(window, point)));
}

/// Hand a built event to its window's `-sendEvent:`, after the local monitors.
pub(crate) fn dispatch(window: Id, event: Id) {
    // Before the window sees it, which is where AppKit runs a local monitor: a
    // monitor exists to swallow an event, and one that ran afterwards could
    // only take it back.
    if !crate::monitor::allows(event) {
        if tracing() {
            eprintln!("rosemary: appkit: a local event monitor swallowed the event");
        }
        return;
    }
    let sel = objc::sel::get("sendEvent:");
    // SAFETY: `-sendEvent:` is `void (id, SEL, NSEvent *)`, and every window
    // has one - this crate installs the default on `NSWindow`.
    unsafe {
        let f: unsafe extern "C" fn(Id, objc::sel::Sel, Id) =
            std::mem::transmute(objc::msg::entry());
        trace_event("dispatch.before", window, event);
        crate::application::with_current_event(event, || {
            input_trace(&format!(
                "stage=dispatch.enter event={event:p} current={:p} current_matches={}",
                crate::application::current_event_id(),
                crate::application::current_event_id() == event,
            ));
            f(window, sel, event);
            input_trace(&format!(
                "stage=dispatch.return event={event:p} current={:p} current_matches={}",
                crate::application::current_event_id(),
                crate::application::current_event_id() == event,
            ));
        });
        input_trace(&format!(
            "stage=dispatch.restored event={event:p} current={:p} current_matches={}",
            crate::application::current_event_id(),
            crate::application::current_event_id() == event,
        ));
    }
}

/// `-[NSWindow sendEvent:]`: route one event to the responder it belongs to.
///
/// The default AppKit routing, and the two halves of it are not the same rule:
/// an event with a position goes to the view under it, and a key event goes to
/// the first responder. Either way the search walks up the responder chain from
/// there, and an event nothing implements is dropped.
/// `ROSEMARY_EVENT_LOG=FILE`: append a line per input event and scripted
/// action to a file.
///
/// Not stderr: a guest which redirects its own - Studio replaces it with its
/// log file once it is running - takes every later trace line with it, and
/// input arrives long after that.
pub const LOG_ENV: &str = "ROSEMARY_EVENT_LOG";
const INPUT_TRACE_ENV: &str = "ROSEMARY_INPUT_TRACE";

static NEXT_INPUT_TRACE_ID: AtomicU64 = AtomicU64::new(1);
static LAST_INPUT_TRACE_ID: AtomicU64 = AtomicU64::new(0);
static LAST_INPUT_TRACE_TIME_US: AtomicU64 = AtomicU64::new(0);
const RECENT_INPUT_TRACE_WINDOW_US: u64 = 250_000;

thread_local! {
    static INPUT_TRACE_ID: std::cell::Cell<u64> = const { std::cell::Cell::new(0) };
}

struct InputTraceScope {
    previous: u64,
}

impl InputTraceScope {
    fn begin() -> Self {
        let previous = INPUT_TRACE_ID.with(std::cell::Cell::get);
        if !input_trace_enabled() {
            return Self { previous };
        }
        let id = NEXT_INPUT_TRACE_ID.fetch_add(1, Ordering::Relaxed);
        LAST_INPUT_TRACE_ID.store(id, Ordering::Relaxed);
        LAST_INPUT_TRACE_TIME_US.store(trace_elapsed_us(), Ordering::Relaxed);
        INPUT_TRACE_ID.with(|active| active.set(id));
        Self { previous }
    }
}

impl Drop for InputTraceScope {
    fn drop(&mut self) {
        INPUT_TRACE_ID.with(|active| active.set(self.previous));
    }
}

fn input_trace_enabled() -> bool {
    static ENABLED: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *ENABLED.get_or_init(|| {
        std::env::var(INPUT_TRACE_ENV)
            .map(|value| value != "" && value != "0")
            .unwrap_or(false)
    })
}

pub(crate) fn input_trace(line: &str) {
    if !input_trace_enabled() {
        return;
    }
    let id = INPUT_TRACE_ID.with(std::cell::Cell::get);
    if id == 0 {
        return;
    }
    input_trace_with_id(id, line);
}

pub(crate) fn input_trace_with_id(id: u64, line: &str) {
    if !input_trace_enabled() || id == 0 {
        return;
    }
    let elapsed_us = trace_elapsed_us();
    debug_log(&format!("input_trace t_us={elapsed_us} id={id} {line}"));
}

fn trace_elapsed_us() -> u64 {
    static START: std::sync::OnceLock<std::time::Instant> = std::sync::OnceLock::new();
    START
        .get_or_init(std::time::Instant::now)
        .elapsed()
        .as_micros()
        .min(u64::MAX as u128) as u64
}

pub(crate) fn recent_input_trace_id() -> u64 {
    if !input_trace_enabled() {
        return 0;
    }
    let now = trace_elapsed_us();
    let last = LAST_INPUT_TRACE_TIME_US.load(Ordering::Relaxed);
    if now.saturating_sub(last) <= RECENT_INPUT_TRACE_WINDOW_US {
        LAST_INPUT_TRACE_ID.load(Ordering::Relaxed)
    } else {
        0
    }
}

pub(crate) fn current_input_trace_id() -> u64 {
    INPUT_TRACE_ID.with(std::cell::Cell::get)
}

fn log_path() -> Option<&'static std::path::Path> {
    static PATH: std::sync::OnceLock<Option<std::path::PathBuf>> = std::sync::OnceLock::new();
    PATH.get_or_init(|| std::env::var_os(LOG_ENV).map(std::path::PathBuf::from))
        .as_deref()
}

pub fn debug_log(line: &str) {
    use std::io::Write;
    let Some(path) = log_path() else {
        return;
    };
    if let Ok(mut file) = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
    {
        let _ = writeln!(file, "{line}");
    }
}

fn trace_event(stage: &str, window: Id, event: Id) {
    if !input_trace_enabled() {
        return;
    }
    let Some(fields) = nsevent::fields_of(event) else {
        input_trace(&format!("stage={stage} event={event:p} fields=unavailable"));
        return;
    };
    let content = window::content_view_of(window);
    let (bounds, frame) = match content.is_null() {
        true => (
            foundation::geometry::NSRect::default(),
            foundation::geometry::NSRect::default(),
        ),
        false => (
            crate::view::bounds_of(content),
            crate::view::frame_of(content),
        ),
    };
    let sdl = window::sdl_windows()
        .into_iter()
        .find(|sdl| window::window_for(*sdl) == window);
    let (window_id, position, size) = sdl.map_or((0, None, None), |sdl| {
        (
            sdl3::video::window_id(sdl),
            window::global_position(sdl),
            sdl3::video::window_size(sdl),
        )
    });
    let scale = window::backing_scale_factor_of(window);
    let current = crate::application::current_event_id();
    input_trace(&format!(
        "stage={stage} event={event:p} current={current:p} current_matches={} window={window:p} sdl_id={window_id} sdl_origin={position:?} sdl_size={size:?} kind={} button={} clicks={} key_code={} repeat={} modifiers={:#x} location_window=({:.3},{:.3}) location_backing=({:.3},{:.3}) delta=({:.3},{:.3}) delta_backing=({:.3},{:.3}) backing_scale={scale:.3} content_frame=({:.3},{:.3},{:.3},{:.3}) content_bounds=({:.3},{:.3},{:.3},{:.3})",
        current == event,
        fields.kind,
        fields.button,
        fields.clicks,
        fields.key_code,
        fields.repeat,
        fields.modifiers,
        fields.location.x,
        fields.location.y,
        fields.location.x * scale,
        fields.location.y * scale,
        fields.delta.x,
        fields.delta.y,
        fields.delta.x * scale,
        fields.delta.y * scale,
        frame.origin.x,
        frame.origin.y,
        frame.size.width,
        frame.size.height,
        bounds.origin.x,
        bounds.origin.y,
        bounds.size.width,
        bounds.size.height,
    ));
}

/// What [`route`] is about to do with an event, for [`LOG_ENV`]: where it is,
/// which tracking area it came from, and the view under it.
fn log_route(window: Id, event: Id, kind: u64) {
    if log_path().is_none() || current_input_trace_id() == 0 {
        return;
    }
    let at = nsevent::location_of(event);
    // SAFETY: null or the content view, which this crate made.
    let hit = unsafe { crate::view::hit_test(window::content_view_of(window), at) };
    // SAFETY: null or a live object this runtime allocated.
    let class = unsafe { objc::object::class_of(hit) }.map_or("-", objc::class::Class::name_str);
    let rect = crate::view::rect_in_window(hit);
    let local = crate::view::point_from_window(hit, at);
    debug_log(&format!(
        "route kind {kind} window {window:p} at ({:.1},{:.1}) area {:p} hit {hit:p} {class} \
         in window ({:.1},{:.1} {:.0}x{:.0}) local ({:.1},{:.1})",
        at.x,
        at.y,
        nsevent::tracking_area_of(event),
        rect.origin.x,
        rect.origin.y,
        rect.size.width,
        rect.size.height,
        local.x,
        local.y,
    ));
    input_trace(&format!(
        "stage=route_location event={event:p} kind={kind} window={window:p} location_window=({:.3},{:.3}) tracking_area={:p} hit={hit:p} hit_class={class} hit_frame=({:.3},{:.3},{:.3},{:.3}) hit_local=({:.3},{:.3})",
        at.x,
        at.y,
        nsevent::tracking_area_of(event),
        rect.origin.x,
        rect.origin.y,
        rect.size.width,
        rect.size.height,
        local.x,
        local.y,
    ));
    if matches!(
        kind,
        kind::LEFT_MOUSE_DOWN | kind::RIGHT_MOUSE_DOWN | kind::OTHER_MOUSE_DOWN
    ) {
        let mut ancestor = hit;
        for depth in 0..12 {
            if ancestor.is_null() {
                break;
            }
            let ancestor_class = unsafe { objc::object::class_of(ancestor) }
                .map_or("-", objc::class::Class::name_str);
            let ancestor_frame = crate::view::rect_in_window(ancestor);
            let ancestor_bounds = crate::view::bounds_of(ancestor);
            debug_log(&format!(
                "route_ancestor depth={depth} view={ancestor:p} class={ancestor_class} frame=({:.1},{:.1},{:.1},{:.1}) bounds=({:.1},{:.1},{:.1},{:.1})",
                ancestor_frame.origin.x,
                ancestor_frame.origin.y,
                ancestor_frame.size.width,
                ancestor_frame.size.height,
                ancestor_bounds.origin.x,
                ancestor_bounds.origin.y,
                ancestor_bounds.size.width,
                ancestor_bounds.size.height,
            ));
            ancestor = unsafe { crate::view::superview_of(ancestor) };
        }
    }
}

pub fn route(window: Id, event: Id) {
    let kind = nsevent::kind_of(event);
    log_route(window, event, kind);
    let Some(selector) = responder_selector(kind) else {
        return;
    };
    let sel = objc::sel::get(selector);
    // A tracking area's events are its owner's, which need not be a view and
    // is not reached by walking up from one.
    let area = nsevent::tracking_area_of(event);
    if !area.is_null() {
        let owner = crate::cursor::tracking_owner_of(area);
        // SAFETY: null or a live object: an owner removes its areas before
        // it goes, as AppKit requires.
        let method = unsafe { objc::object::class_of(owner) }.and_then(|c| c.method(sel));
        if tracing() {
            eprintln!(
                "rosemary: appkit: -{selector} to tracking area owner {owner:p}{}",
                match method.is_some() {
                    true => "",
                    false => " - NOT implemented",
                }
            );
        }
        if let Some(method) = method {
            let receiver_class = unsafe { objc::object::class_of(owner) };
            let method_owner = receiver_class.and_then(|class| {
                class.chain().find(|class| {
                    class
                        .own_method(sel)
                        .is_some_and(|candidate| std::ptr::eq(candidate, method))
                })
            });
            input_trace(&format!(
                "stage=route_call selector={selector} receiver={owner:p} receiver_class={} method_owner={} imp={:p} event={event:p} current_matches={}",
                receiver_class.map_or("none", objc::class::Class::name_str),
                method_owner.map_or("none", objc::class::Class::name_str),
                method.implementation(),
                crate::application::current_event_id() == event,
            ));
            let started = std::time::Instant::now();
            // SAFETY: every tracking method is `void (id, SEL, NSEvent *)`.
            unsafe {
                let f: unsafe extern "C" fn(Id, objc::sel::Sel, Id) =
                    std::mem::transmute(method.implementation());
                f(owner, sel, event);
            }
            input_trace(&format!(
                "stage=route_return selector={selector} receiver={owner:p} event={event:p} elapsed_us={}",
                started.elapsed().as_micros(),
            ));
        } else {
            input_trace(&format!(
                "stage=route_target selector={selector} receiver={owner:p} result=unhandled event={event:p} current_matches={}",
                crate::application::current_event_id() == event,
            ));
        }
        return;
    }
    let start = match positional(kind) {
        // SAFETY: null or the content view, which this crate made.
        true => unsafe {
            crate::view::hit_test(window::content_view_of(window), nsevent::location_of(event))
        },
        false => responder_of(window),
    };
    let Some((responder, method)) = chain(start, sel) else {
        if matches!(
            kind,
            kind::LEFT_MOUSE_DOWN
                | kind::LEFT_MOUSE_UP
                | kind::RIGHT_MOUSE_DOWN
                | kind::RIGHT_MOUSE_UP
                | kind::OTHER_MOUSE_DOWN
                | kind::OTHER_MOUSE_UP
        ) {
            debug_log(&format!(
                "route target kind {kind} selector {selector} start {start:p} none"
            ));
        }
        if tracing() {
            eprintln!("rosemary: appkit: -{selector}: nothing from {start:p} up implements it");
        }
        input_trace(&format!(
            "stage=route_target selector={selector} start={start:p} result=unhandled event={event:p} current_matches={}",
            crate::application::current_event_id() == event,
        ));
        return;
    };
    if matches!(
        kind,
        kind::LEFT_MOUSE_DOWN
            | kind::LEFT_MOUSE_UP
            | kind::RIGHT_MOUSE_DOWN
            | kind::RIGHT_MOUSE_UP
            | kind::OTHER_MOUSE_DOWN
            | kind::OTHER_MOUSE_UP
    ) {
        let class = unsafe { objc::object::class_of(responder) };
        debug_log(&format!(
            "route target kind {kind} selector {selector} responder {responder:p} class {}",
            class.map_or("no class", |class| class.name_str()),
        ));
    }
    if tracing() {
        // SAFETY: a live object this runtime allocated.
        let class = unsafe { objc::object::class_of(responder) };
        eprintln!(
            "rosemary: appkit: -{selector} to {responder:p} ({})",
            class.map_or("no class", |c| c.name_str()),
        );
    }
    let receiver_class = unsafe { objc::object::class_of(responder) };
    let method_owner = receiver_class.and_then(|class| {
        class.chain().find(|class| {
            class
                .own_method(sel)
                .is_some_and(|candidate| std::ptr::eq(candidate, method))
        })
    });
    input_trace(&format!(
        "stage=route_call selector={selector} start={start:p} receiver={responder:p} receiver_class={} method_owner={} imp={:p} event={event:p} current_matches={}",
        receiver_class.map_or("none", objc::class::Class::name_str),
        method_owner.map_or("none", objc::class::Class::name_str),
        method.implementation(),
        crate::application::current_event_id() == event,
    ));
    let started = std::time::Instant::now();
    // SAFETY: every responder method here is `void (id, SEL, NSEvent *)`.
    unsafe {
        let f: unsafe extern "C" fn(Id, objc::sel::Sel, Id) =
            std::mem::transmute(method.implementation());
        f(responder, sel, event);
    }
    input_trace(&format!(
        "stage=route_return selector={selector} receiver={responder:p} event={event:p} elapsed_us={}",
        started.elapsed().as_micros(),
    ));
}

/// The responder method an event type is delivered through.
fn responder_selector(kind: u64) -> Option<&'static str> {
    Some(match kind {
        kind::LEFT_MOUSE_DOWN => "mouseDown:",
        kind::LEFT_MOUSE_UP => "mouseUp:",
        kind::RIGHT_MOUSE_DOWN => "rightMouseDown:",
        kind::RIGHT_MOUSE_UP => "rightMouseUp:",
        kind::OTHER_MOUSE_DOWN => "otherMouseDown:",
        kind::OTHER_MOUSE_UP => "otherMouseUp:",
        kind::MOUSE_MOVED => "mouseMoved:",
        kind::LEFT_MOUSE_DRAGGED => "mouseDragged:",
        kind::RIGHT_MOUSE_DRAGGED => "rightMouseDragged:",
        kind::OTHER_MOUSE_DRAGGED => "otherMouseDragged:",
        kind::MOUSE_ENTERED => "mouseEntered:",
        kind::MOUSE_EXITED => "mouseExited:",
        kind::CURSOR_UPDATE => "cursorUpdate:",
        kind::SCROLL_WHEEL => "scrollWheel:",
        kind::KEY_DOWN => "keyDown:",
        kind::KEY_UP => "keyUp:",
        kind::FLAGS_CHANGED => "flagsChanged:",
        _ => return None,
    })
}

/// Whether an event is about a place rather than about the keyboard.
fn positional(kind: u64) -> bool {
    !matches!(kind, kind::KEY_DOWN | kind::KEY_UP | kind::FLAGS_CHANGED)
}

/// Walk the responder chain from `start` for something that implements `sel`.
///
/// The chain is the superview chain and then the window, which is AppKit's for
/// a view in a window. Bounded, because a subview list a guest built with a
/// cycle in it would otherwise hang inside event delivery.
fn chain(start: Id, sel: objc::sel::Sel) -> Option<(Id, &'static objc::class::Method)> {
    let mut responder = start;
    let mut fallback = None;
    for _ in 0..64 {
        if responder.is_null() {
            return fallback;
        }
        // SAFETY: null or a live object this runtime allocated.
        if let Some(method) =
            unsafe { objc::object::class_of(responder) }.and_then(|c| c.method(sel))
        {
            let ours = crate::text::is_default_key_handling(method.implementation() as *const ());
            match ours {
                false => return Some((responder, method)),
                true => fallback = fallback.or(Some((responder, method))),
            }
        }
        let next = unsafe { crate::view::superview_of(responder) };
        responder = match next.is_null() {
            true => unsafe { crate::view::window_of(responder) },
            false => next,
        };
    }
    fallback
}

/// Where the pointer was last seen, in SDL's window coordinates.
///
/// A wheel event carries no position and a click carries one only where SDL
/// filled it in, so the last motion is what says which view the event is about.
static POINTER: std::sync::Mutex<(f32, f32)> = std::sync::Mutex::new((0.0, 0.0));

/// Record a programmatic cursor warp in window coordinates.
///
/// SDL does not deliver a motion event for an in-window warp while relative
/// mode is active. Without this explicit update, the cursor moves to an app's
/// lock point but every `NSEvent` and `+[NSEvent mouseLocation]` continues to
/// report the position from before the lock.
pub(crate) fn warp_pointer(x: f32, y: f32) {
    *POINTER.lock().unwrap_or_else(|e| e.into_inner()) = (x, y);
}

/// Where a physical warp is expected to be echoed back as a motion event.
///
/// CoreGraphics posts no event for a warp, but SDL does (Cocoa sends one
/// synchronously, X11 reports the server's MotionNotify), with a delta of
/// `target - previous`. A game that recentres the cursor after every
/// `-mouseMoved:` would read that delta as the player undoing their own motion.
#[derive(Clone, Copy)]
struct WarpEcho {
    from: (f32, f32),
    to: (f32, f32),
    armed_at: Instant,
}

#[derive(Clone, Copy, Debug, PartialEq)]
enum WarpEchoResult {
    None,
    Consumed {
        target: (f32, f32),
    },
    Adjusted {
        target: (f32, f32),
        delta: (f32, f32),
    },
}

const WARP_ECHO_LIFETIME: Duration = Duration::from_millis(50);
const WARP_ECHO_RESIDUAL_LIMIT: f32 = 32.0;
const WARP_ECHO_DELTA_TOLERANCE: f32 = 2.0;
const MAX_PENDING_WARP_ECHOES: usize = 32;

static WARP_ECHOES: std::sync::Mutex<VecDeque<WarpEcho>> = std::sync::Mutex::new(VecDeque::new());

/// Swallow the next motion event that lands on `to`, in window coordinates.
/// Nothing is armed when `from` is already there: SDL drops a warp that moves
/// nothing, and a stale echo would eat the next real motion to reach `to`.
pub(crate) fn expect_warp_echo(from: (f32, f32), to: (f32, f32)) {
    let echo = (!lands_on(from, to)).then_some(to);
    let trace_id = match current_input_trace_id() {
        0 => recent_input_trace_id(),
        id => id,
    };
    input_trace_with_id(
        trace_id,
        &format!("stage=warp_echo_armed from={from:?} to={to:?} expected={echo:?}"),
    );
    if echo.is_some() {
        enqueue_warp_echo(
            &mut WARP_ECHOES.lock().unwrap_or_else(|e| e.into_inner()),
            from,
            to,
            Instant::now(),
        );
    }
}

fn pending_warp_target() -> Option<(f32, f32)> {
    WARP_ECHOES
        .lock()
        .unwrap_or_else(|e| e.into_inner())
        .back()
        .map(|echo| echo.to)
}

fn take_warp_echo(x: f32, y: f32, dx: f32, dy: f32) -> WarpEchoResult {
    let now = Instant::now();
    let mut echoes = WARP_ECHOES.lock().unwrap_or_else(|e| e.into_inner());
    take_warp_echo_from_queue(&mut echoes, x, y, dx, dy, now)
}

fn enqueue_warp_echo(
    echoes: &mut VecDeque<WarpEcho>,
    from: (f32, f32),
    to: (f32, f32),
    now: Instant,
) {
    discard_expired_warp_echoes(echoes, now);
    echoes.push_back(WarpEcho {
        from,
        to,
        armed_at: now,
    });
    while echoes.len() > MAX_PENDING_WARP_ECHOES {
        echoes.pop_front();
    }
}

fn take_warp_echo_from_queue(
    echoes: &mut VecDeque<WarpEcho>,
    x: f32,
    y: f32,
    dx: f32,
    dy: f32,
    now: Instant,
) -> WarpEchoResult {
    discard_expired_warp_echoes(echoes, now);

    if let Some(index) = echoes.iter().position(|echo| lands_on(echo.to, (x, y))) {
        let echo = echoes
            .remove(index)
            .expect("warp echo index came from this queue");
        return WarpEchoResult::Consumed { target: echo.to };
    }

    let adjusted = echoes.iter().enumerate().find_map(|(index, echo)| {
        let residual = (x - echo.to.0, y - echo.to.1);
        let expected_delta = (echo.to.0 - echo.from.0, echo.to.1 - echo.from.1);
        let observed_from_warp = (x - echo.from.0, y - echo.from.1);
        let delta_matches_warp = (dx - observed_from_warp.0).abs() <= WARP_ECHO_DELTA_TOLERANCE
            && (dy - observed_from_warp.1).abs() <= WARP_ECHO_DELTA_TOLERANCE;
        let residual_is_small = residual.0.abs() <= WARP_ECHO_RESIDUAL_LIMIT
            && residual.1.abs() <= WARP_ECHO_RESIDUAL_LIMIT;

        (residual_is_small && delta_matches_warp).then_some((index, echo.to, expected_delta))
    });

    if let Some((index, target, expected_delta)) = adjusted {
        echoes.remove(index);
        return WarpEchoResult::Adjusted {
            target,
            delta: (dx - expected_delta.0, dy - expected_delta.1),
        };
    }

    WarpEchoResult::None
}

fn discard_expired_warp_echoes(echoes: &mut VecDeque<WarpEcho>, now: Instant) {
    echoes.retain(|echo| {
        now.checked_duration_since(echo.armed_at)
            .is_some_and(|age| age <= WARP_ECHO_LIFETIME)
    });
}

/// Within half a pixel: SDL converts between desktop and window coordinates.
fn lands_on(target: (f32, f32), point: (f32, f32)) -> bool {
    (target.0 - point.0).abs() < 0.5 && (target.1 - point.1).abs() < 0.5
}

/// The last cursor position an event or programmatic warp established.
pub(crate) fn pointer_position() -> (f32, f32) {
    *POINTER.lock().unwrap_or_else(|e| e.into_inner())
}

/// Record where an event says the pointer is, and answer where a guest is to be
/// told it is.
///
/// The two differ only while the pointer is disassociated, and then they differ
/// for every event and not only for motion: CoreGraphics leaves the cursor
/// exactly where it was, so a click and a wheel turn arrive at that point too.
/// SDL keeps tracking a position inside the window through relative mode, and a
/// click that took SDL's answer would move the frozen point to somewhere the
/// cursor never was - which is a hit test, and so a first responder, against the
/// wrong view.
fn track_pointer(window: u32, x: f32, y: f32) -> (f32, f32) {
    if !crate::screen::mouse_is_associated() {
        return pointer_position();
    }
    POINTER_WINDOW.store(window, std::sync::atomic::Ordering::Relaxed);
    let mut pointer = POINTER.lock().unwrap_or_else(|e| e.into_inner());
    *pointer = (x, y);
    *pointer
}

/// Where the guest is to be told the pointer is on the desktop, for the calls
/// that ask the window system rather than reading an event.
pub(crate) fn desktop_pointer() -> Option<(f32, f32)> {
    let id = POINTER_WINDOW.load(std::sync::atomic::Ordering::Relaxed);
    if id == 0 {
        return None;
    }
    let sdl = window::sdl_windows()
        .into_iter()
        .find(|window| sdl3::video::window_id(*window) == id)?;
    let (origin_x, origin_y) = window::global_position(sdl)?;
    let (x, y) = pointer_position();
    Some((x + origin_x as f32, y + origin_y as f32))
}

pub(crate) fn frozen_pointer() -> Option<(f32, f32)> {
    if crate::screen::mouse_is_associated() {
        return None;
    }
    desktop_pointer()
}

/// The SDL id of the window the last pointer event came from; `0` before any.
static POINTER_WINDOW: std::sync::atomic::AtomicU32 = std::sync::atomic::AtomicU32::new(0);

/// The window [`POINTER`] is relative to: the one the pointer was last seen
/// in, not the first one made. A game with a splash window still open would
/// otherwise translate every desktop point against the splash.
pub(crate) fn pointer_window() -> Option<sdl3::Window> {
    let windows = window::sdl_windows();
    let id = POINTER_WINDOW.load(std::sync::atomic::Ordering::Relaxed);
    windows
        .iter()
        .copied()
        .find(|w| id != 0 && sdl3::video::window_id(*w) == id)
        .or_else(|| windows.first().copied())
}

/// Whether `-mouseMoved:` should be delivered at all.
fn wants_mouse_moved(window: Id) -> bool {
    // SAFETY: null or the content view, which this crate made.
    window::accepts_mouse_moved_events(window)
        || unsafe { crate::view::any_tracking_area(window::content_view_of(window)) }
}

/// The object an input event goes to: the window's first responder, or its
/// content view when nothing has been made one.
///
/// `-firstResponder` answers with the window itself at the end of its own
/// chain, and a window is not what draws - so that answer means "the view".
fn responder_of(window: Id) -> Id {
    let sel = objc::sel::get("firstResponder");
    // SAFETY: `-firstResponder` is `id (id, SEL)` on a window this crate made.
    let responder = unsafe {
        let f: unsafe extern "C" fn(Id, objc::sel::Sel) -> Id =
            std::mem::transmute(objc::msg::entry());
        f(window, sel)
    };
    match responder == window || responder.is_null() {
        true => window::content_view_of(window),
        false => responder,
    }
}

/// The `NSWindow` an SDL window id names.
///
/// SDL identifies a window by a small integer in an event and by a pointer
/// everywhere else, and `crates/sdl3` does not expose the mapping - so this
/// walks the windows this crate made and asks each one. There are never more
/// than a handful.
pub(crate) fn object_for(id: u32) -> Id {
    for object in window::all() {
        // SAFETY: a window this crate made.
        let sdl = unsafe { window::sdl_window(object) };
        if !sdl.is_null() && sdl3::video::window_id(sdl) == id {
            return object;
        }
    }
    std::ptr::null_mut()
}

/// Post a window notification, to the centre and to the window's delegate.
///
/// Both, for the reason `-finishLaunching` sends the application's delegate
/// method directly as well: AppKit registers a window's delegate for the
/// notifications it declares the moment it is set, so a program that only
/// implements `-windowDidResize:` never registers as an observer of anything.
/// Set to print every window notification, and whether anything took it.
///
/// A window event that reaches nobody is invisible from both ends - the program
/// simply does not react - and a release build inlines every function on this
/// path, so a breakpoint cannot answer it either. This is the answer: the name,
/// the window, its delegate, and whether that delegate implements the method.
pub const TRACE_ENV: &str = "ROSEMARY_TRACE_EVENT";

pub(crate) fn tracing() -> bool {
    static ON: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *ON.get_or_init(|| std::env::var_os(TRACE_ENV).is_some())
}

fn post(id: u32, name: &str) {
    let object = object_for(id);
    if object.is_null() {
        if tracing() {
            eprintln!("rosemary: appkit: {name}: SDL window {id} is no window this crate made");
        }
        return;
    }
    post_for(object, name);
}

/// Send the window notification `name` about `object` to its delegate and to
/// observers.
pub(crate) fn post_for(object: Id, name: &str) {
    let delegate = window::delegate_of(object);
    if tracing() {
        eprintln!("rosemary: appkit: {name}: window {object:p}, delegate {delegate:p}");
    }
    if !delegate.is_null() {
        let selector = delegate_selector(name);
        let notification = foundation::notification::make(name, object, std::ptr::null_mut());
        // SAFETY: a window delegate method is
        // `void (id, SEL, NSNotification *)`.
        let sel = objc::sel::get(selector);
        // SAFETY: null or a live object this runtime allocated.
        let method = unsafe { objc::object::class_of(delegate) }.and_then(|c| c.method(sel));
        if tracing() {
            eprintln!(
                "rosemary: appkit:   -{selector} is {}",
                match method.is_some() {
                    true => "implemented by the delegate",
                    false => "NOT implemented by the delegate",
                }
            );
        }
        if let Some(method) = method {
            // SAFETY: the prototype above.
            unsafe {
                let f: unsafe extern "C" fn(Id, objc::sel::Sel, Id) =
                    std::mem::transmute(method.implementation());
                f(delegate, sel, notification);
            }
        }
    }
    foundation::notification::post(name, object, std::ptr::null_mut());
}

/// The delegate method a notification name goes with.
///
/// The mapping is Apple's and is not derivable: `NSWindowDidResizeNotification`
/// is `-windowDidResize:`, which is the name without `NS` and without
/// `Notification` - but only because every one of them happens to be, and a
/// table is what makes that a decision rather than a coincidence.
fn delegate_selector(name: &str) -> &'static str {
    match name {
        window::DID_RESIZE => "windowDidResize:",
        window::DID_MOVE => "windowDidMove:",
        window::DID_CHANGE_SCREEN => "windowDidChangeScreen:",
        window::WILL_CLOSE => "windowWillClose:",
        window::DID_BECOME_KEY => "windowDidBecomeKey:",
        window::DID_RESIGN_KEY => "windowDidResignKey:",
        window::DID_BECOME_MAIN => "windowDidBecomeMain:",
        window::DID_RESIGN_MAIN => "windowDidResignMain:",
        window::DID_MINIATURIZE => "windowDidMiniaturize:",
        window::DID_DEMINIATURIZE => "windowDidDeminiaturize:",
        window::WILL_ENTER_FULL_SCREEN => "windowWillEnterFullScreen:",
        window::WILL_EXIT_FULL_SCREEN => "windowWillExitFullScreen:",
        window::DID_ENTER_FULL_SCREEN => "windowDidEnterFullScreen:",
        window::DID_EXIT_FULL_SCREEN => "windowDidExitFullScreen:",
        window::DID_CHANGE_BACKING_PROPERTIES => "windowDidChangeBackingProperties:",
        window::WILL_START_LIVE_RESIZE => "windowWillStartLiveResize:",
        window::DID_END_LIVE_RESIZE => "windowDidEndLiveResize:",
        other => objc::fail!("appkit::event: {other} has no delegate method in this table"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn a_programmatic_warp_updates_the_reported_pointer() {
        let previous = pointer_position();
        warp_pointer(320.0, 240.0);
        let warped = pointer_position();
        *POINTER.lock().unwrap_or_else(|e| e.into_inner()) = previous;

        assert_eq!(warped, (320.0, 240.0));
    }

    #[test]
    fn a_warp_echo_is_taken_once() {
        let mut echoes = VecDeque::new();
        let now = Instant::now();
        assert_eq!(
            take_warp_echo_from_queue(&mut echoes, 400.0, 300.0, 0.0, 0.0, now),
            WarpEchoResult::None
        );
        enqueue_warp_echo(&mut echoes, (0.0, 0.0), (400.0, 300.0), now);
        assert_eq!(
            take_warp_echo_from_queue(&mut echoes, 435.0, 300.0, 435.0, 300.0, now),
            WarpEchoResult::None
        );
        assert_eq!(
            take_warp_echo_from_queue(&mut echoes, 400.2, 299.9, 400.2, 299.9, now),
            WarpEchoResult::Consumed {
                target: (400.0, 300.0)
            }
        );
        assert_eq!(
            take_warp_echo_from_queue(&mut echoes, 400.0, 300.0, 0.0, 0.0, now),
            WarpEchoResult::None
        );
    }

    #[test]
    fn a_warp_echo_with_late_pointer_motion_only_delivers_the_real_motion() {
        let mut echoes = VecDeque::new();
        let now = Instant::now();
        let from = (1320.973, 392.012);
        let target = (1416.0, 369.0);
        enqueue_warp_echo(&mut echoes, from, target, now);

        let event = (1429.0, 365.0);
        let result =
            take_warp_echo_from_queue(&mut echoes, event.0, event.1, 108.027, -27.012, now);
        match result {
            WarpEchoResult::Adjusted {
                target: adjusted_target,
                delta,
            } => {
                assert_eq!(adjusted_target, target);
                assert!((delta.0 - (event.0 - target.0)).abs() < 0.001);
                assert!((delta.1 - (event.1 - target.1)).abs() < 0.001);
            }
            other => panic!("unexpected warp result: {other:?}"),
        }
    }

    #[test]
    fn a_real_move_near_an_old_warp_target_is_not_reduced() {
        let mut echoes = VecDeque::new();
        let now = Instant::now();
        enqueue_warp_echo(&mut echoes, (1330.0, 375.0), (1416.0, 369.0), now);
        assert_eq!(
            take_warp_echo_from_queue(&mut echoes, 1385.785, 375.805, -5.398, 0.0, now,),
            WarpEchoResult::None
        );
    }

    #[test]
    fn camera_motion_is_scaled_only_while_captured_or_right_dragging() {
        let right = sdl3::mouse::mask(sdl3::mouse::RIGHT);
        assert_eq!(mouse_look_delta_scale(right, true), 0.003);
        assert_eq!(mouse_look_delta_scale(0, false), 0.003);
        assert_eq!(mouse_look_delta_scale(0, true), 1.0);
        assert_eq!(
            mouse_look_delta_scale(sdl3::mouse::mask(sdl3::mouse::LEFT), true),
            1.0
        );
    }

    /// Every name this crate publishes has a delegate method, so a notification
    /// cannot be posted with nowhere to send it.
    #[test]
    fn every_window_notification_has_a_delegate_method() {
        for name in crate::NOTIFICATION_NAMES {
            if name.starts_with("NSWindow") {
                assert!(!delegate_selector(name).is_empty(), "{name}");
            }
        }
    }
}
