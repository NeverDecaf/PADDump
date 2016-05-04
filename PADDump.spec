# -*- mode: python -*-

block_cipher = None


a = Analysis(['PADDump.py'],
             pathex=['C:\\Users\\User\\Desktop\\Stuff\\Git\\PADDump'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
			 
#a.binaries+=[('WinDivert.dll','WinDivert.dll','BINARY')]

#Tree(r'DLLs', prefix=r'DLLs')


#os.path.join(sys.exec_prefix, "DLLs", "WinDivert.dll")
import sys
#a.datas+=[(os.path.join(sys.exec_prefix, "DLLs", "WinDivert.dll"),'/DLLs/WinDivert.dll')]
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
		  [('/DLLs/WinDivert.dll',os.path.join(sys.exec_prefix, "DLLs", "WinDivert.dll"),'BINARY')],
		  #Tree(r'DLLs', prefix=r'DLLs'),
		  #[('WinDivert.dll','WinDivert.dll','BINARY')],
          name='PADDump',
          debug=False,
          strip=False,
          upx=True,
          console=True )
