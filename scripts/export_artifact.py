"""Copy ABI + bytecode from Foundry's build output into the committed artifact files."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src = json.loads((ROOT / "chain/out/PassportRegistry.sol/PassportRegistry.json").read_text())
out = {
    "contractName": "PassportRegistry",
    "abi": src["abi"],
    "bytecode": src["bytecode"]["object"],
    "compiler": "solc 0.8.26, optimizer 200 runs, evm paris",
}
for target in ("chain/artifacts/PassportRegistry.json", "backend/apps/chain/artifacts/PassportRegistry.json"):
    (ROOT / target).write_text(json.dumps(out, indent=1))
print("artifacts updated")
