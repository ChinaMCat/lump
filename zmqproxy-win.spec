# -*- mode: python -*-

block_cipher = pyi_crypto.PyiBlockCipher(key='Bye-bye my love.')


a = Analysis(['zmqproxy.py'],
             pathex=['/home/xy/work/python/lump'],
             binaries=None,
             datas=None,
             hiddenimports=['zmq'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='zmqproxy',
          debug=False,
          strip=False,
          upx=False,
          console=True , icon='static\\image\\bats.ico', version='file_ver_zp.txt')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='zmqproxy-win')
