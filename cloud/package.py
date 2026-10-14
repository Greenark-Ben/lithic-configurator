"""Build the private APS payload after dotnet build -c Release.
The licensed Revit template is a local input, never a public browser asset.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import zipfile
parser = argparse.ArgumentParser()
parser.add_argument('--template', required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
native = root.parent / 'public/native'
binary = root / 'bin/Release/net48'
contents = root / 'package/LithicAfkcCloud.bundle/Contents'
contents.mkdir(parents=True, exist_ok=True)
for file in binary.glob('*.dll'):
    if not file.name.lower().startswith('revitapi'):
        shutil.copy2(file, contents / file.name)
if not (contents / 'Lithic.Afkc.Cloud.dll').exists():
    raise ValueError('Build the .NET add-in before packaging.')
library = binary / 'Lib'
if not library.exists():
    library = Path.home() / '.nuget/packages/ironpython.stdlib/2.7.12/content/Lib'
shutil.copytree(library, contents / 'Lib', dirs_exist_ok=True)
for name in ['authoring.py', 'drawings.py']:
    text = (native / name).read_text(encoding='utf-8')
    changed = text.replace('from pyrevit import DB', 'import Autodesk.Revit.DB as DB')
    if changed == text: raise ValueError('Expected desktop DB import missing.')
    (contents / name).write_text(changed, encoding='utf-8')
for name in ['contract.py', 'afkc-source.json']:
    shutil.copy2(native / name, contents / name)
text = (native / 'script.py').read_text(encoding='utf-8').split('\ndef main():\n')[0]
text = text.replace('from pyrevit import DB, forms, revit', 'import Autodesk.Revit.DB as DB')
text = text.replace("result['drawingEvidence'] = export_review_views(project,views,output,label)", "result['drawingEvidence'] = []  # Images await desktop review")
text = text.replace("result['visualReviewStatus'] = 'exported-views-await-visual-review'", "result['visualReviewStatus'] = 'not-exported-headless-awaiting-Revit-review'")
text = text.replace(' and document.PathName != revit.uidoc.Document.PathName', '')
if 'revit.' in text or 'forms.' in text: raise ValueError('Desktop dependency remains.')
(contents / 'cloud_builder.py').write_text(text, encoding='utf-8')
shutil.copy2(root / 'cloud_entry.py', contents / 'cloud_entry.py')
shutil.copy2(root / 'PackageContents.xml', contents.parent / 'PackageContents.xml')
shutil.copy2(root / 'Lithic.Afkc.Cloud.addin', contents / 'Lithic.Afkc.Cloud.addin')
artifacts = root / 'artifacts'
artifacts.mkdir(exist_ok=True)
with zipfile.ZipFile(artifacts / 'appbundle.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    for file in contents.parent.rglob('*'):
        if file.is_file(): archive.write(file, file.relative_to(root / 'package').as_posix())
shutil.copy2(Path(args.template), artifacts / 'window.rft')
manifest = {'adapter':'lithic-afkc-aps-browser/0.2','sourceBuilder':'lithic-afkc-desktop/0.2.2','engine':'Autodesk.Revit+2024','files':{name:hashlib.sha256((artifacts / name).read_bytes()).hexdigest() for name in ['appbundle.zip','window.rft']}}
(root / 'artifacts-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print('Private APS artifacts packaged; desktop geometry functions retained.')
