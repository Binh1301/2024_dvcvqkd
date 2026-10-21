"""Local TeX compilation only; no scientific execution or external upload."""
import hashlib
import json
from pathlib import Path
import subprocess

OUT=Path(__file__).resolve().parent
COMPILER=Path('C:/Users/HP/.codex/tools/manuscript-tex-20261020/tectonic.exe')


def main():
    if (OUT/'validation/final_receipt.json').exists():raise FileExistsError('Sealed manuscript is immutable')
    command=[str(COMPILER),'--keep-logs','--keep-intermediates','main.tex']
    result=subprocess.run(command,cwd=OUT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (OUT/'validation/build_console.txt').write_bytes(result.stdout)
    record=dict(command=command,exit_code=result.returncode,
        compiler_sha256=hashlib.sha256(COMPILER.read_bytes()).hexdigest(),
        main_tex_sha256=hashlib.sha256((OUT/'main.tex').read_bytes()).hexdigest())
    (OUT/'validation/build_receipt.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(result.stdout.decode('utf-8',errors='replace'))
    if result.returncode:raise RuntimeError('TeX build failed; see captured console')


if __name__=='__main__':main()
