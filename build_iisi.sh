#!/bin/bash

sudo chown -R xy:xy .
# rm -rf build/pytcs build/pytcs-setup dist/pytcs dist/pytcs-setup
python build_iisi.py
# pyinstaller --clean -y pytcs.spec

chmod a-x dist/iisi/*.so*
upx dist/iisi/iisi

pyinstaller --clean -y iisi-setup.spec
tar -Jcvf dist/iisi-setup/_imps.so -C dist/ iisi
chmod a-x dist/iisi-setup/*.so*

rm -rf ~/Downloads/iisi_setup.tar.gz
tar zcvf ~/Downloads/iisi_setup.tar.gz -C dist/ iisi-setup

scp ~/Downloads/iisi_setup.tar.gz cos83:/tmp
scp ~/Downloads/iisi_setup.tar.gz wgq:/tmp
