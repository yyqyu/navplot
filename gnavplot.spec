# -*- mode: python -*-
a = Analysis(['navplot\\gnavplot.py'],
             pathex=['C:\\Users\\ahs\\Desktop\\navplot'],
             hiddenimports=['reportlab.rl_settings'],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)

dict_tree = Tree("navplot/data", prefix = "data")

exe = EXE(pyz,
          a.scripts,
          a.binaries + dict_tree,
          a.zipfiles,
          a.datas,
          name='gnavplot.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False )
