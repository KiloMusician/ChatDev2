#!/usr/bin/env python3
from fastapi import FastAPI
from pydantic import BaseModel
from gdtoolkit.parser import parser as gdparser
import ast

app = FastAPI()

class Snippet(BaseModel):
    code: str

# ---- Python -> GDScript (subset) ----
def py_to_gd(code: str) -> str:
    tree = ast.parse(code)
    out = []

    def emit(line=""): out.append(line)
    def expr_to_gd(e):
        if isinstance(e, ast.Name): return e.id
        if isinstance(e, ast.Constant): return repr(e.value)
        if isinstance(e, ast.BinOp) and isinstance(e.op, ast.Add):
            return f"{expr_to_gd(e.left)} + {expr_to_gd(e.right)}"
        return "/*TODO*/"

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            args = ", ".join(a.arg for a in node.args.args)
            emit(f"func {node.name}({args}):")
            for s in node.body:
                if isinstance(s, ast.Assign) and len(s.targets)==1:
                    emit(f"    {s.targets[0].id} = {expr_to_gd(s.value)}")
                elif isinstance(s, ast.Return):
                    emit(f"    return {expr_to_gd(s.value) if s.value else ''}")
                elif isinstance(s, ast.For) and isinstance(s.target, ast.Name):
                    # for i in range(n)
                    if isinstance(s.iter, ast.Call) and hasattr(s.iter.func, 'id') and s.iter.func.id=="range":
                        arg0 = expr_to_gd(s.iter.args[0]) if s.iter.args else "0"
                        arg1 = expr_to_gd(s.iter.args[1]) if len(s.iter.args)>1 else arg0
                        emit(f"    for {s.target.id} in range({arg0}, {arg1}):")
                        for bs in s.body:
                            if isinstance(bs, ast.Expr) and isinstance(bs.value, ast.Call):
                                call = bs.value
                                name = call.func.id if hasattr(call.func, 'id') else "call"
                                args = ", ".join(expr_to_gd(a) for a in call.args)
                                emit(f"        {name}({args})")
            emit("")
        elif isinstance(node, ast.Assign) and len(node.targets)==1:
            emit(f"{node.targets[0].id} = {expr_to_gd(node.value)}")
        else:
            emit("# TODO: unsupported stmt")

    return "\n".join(out).strip() + "\n"

# ---- GDScript -> Python (very light sketch) ----
def gd_to_py(code: str) -> str:
    # parse or bail
    try:
        gdparser.parse(code)
    except Exception:
        return "# Parse error; returning as comment for now\n" + "\n".join("# "+l for l in code.splitlines())

    py_lines = []
    for line in code.splitlines():
        if line.strip().startswith("func "):
            sig = line.strip()[5:]
            name = sig.split("(")[0]
            args = sig.split("(")[1].split(")")[0]
            py_lines.append(f"def {name}({args}):")
        elif line.strip().startswith("#") or line.strip()=="":
            py_lines.append(line)
        else:
            py_lines.append("    " + line)
    return "\n".join(py_lines) + "\n"

@app.post("/py2gd")
def api_py2gd(s: Snippet):
    return {"gdscript": py_to_gd(s.code)}

@app.post("/gd2py")
def api_gd2py(s: Snippet):
    return {"python": gd_to_py(s.code)}

@app.get("/health")
def health():
    return {"status": "ok", "service": "gdtranslate", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7878)