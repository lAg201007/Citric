# Snapshots de patch

Os arquivos no diretório patches foram preservados da sessão de Rosemary:

- 0001-nsview-clips-to-bounds.patch: mudança de clipping de NSView/backing.
- 0001-rosemary-appkit-runloop-objc.patch: snapshot agregado das mudanças iniciais de AppKit, run loop e ARC.
- 0001-rosemary-compatibility-experiment.patch: snapshot experimental mais amplo da camada de compatibilidade.

Os nomes se sobrepõem e alguns trechos podem estar duplicados. Eles são registros para inspeção e não uma sequência segura de cherry-pick ou git am. O estado canônico é o código atual em crates/ e seu diff em relação ao commit base. Consulte docs/compatibility.md para a motivação e o resultado conhecido.
