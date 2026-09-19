# from utils import build_path
# from models import stage
#
# _STAGES: dict[str, Stage] = [] # fill in as i add stages
#
# _ACTIONS_SUFFIX: dict[str, str] = ["-w": "test", "-g": "golden"]
#
# def loader(doc, consumes) -> str:
#   path = build_path(consumes, doc, "golden", STAGES[consumes].suffix)
#   return read_text(path)
#
# def chain(current_stage) -> list[str]:
#   keys = []
#   while current_stage is not None:
#       keys.append(current_stage)
#       current_stage = STAGES[current_stage].consumes
#   return reversed(keys)
#
# def runner(doc, current_stage) -> could be almost anything:
#   output = None
#   for key in chain(current_stage)[:-1]:
#       output = STAGES[key].opperation(doc, output)
#   return output
#
# def get_input(doc, current_stage, mode) -> could be anything:
#   if mode == golden:
#       return loader(doc, STAGES[current_stage].consumes)
#   else:
#       return runner(doc)
#
# def write_file(doc, stage, mode, output) -> None:
#   path = build_path(stage, doc, _ACTIONS_SUFFIX[mode], stage.suffix)
#   text = stage.to_text(output)
#   path.write_text(text)
#
# def build_cli():
#   parser = argparse.ArgumentParser(description=stage.stage_description)
#   parser.add_argument("stage", choices=STAGES.keys(), help="The stage you want to run")
#   parser.add_argument("doc", choices=TOOLBELT_REGISTRY.keys(), help="the name of the document")
#   parser.add_argument("mode", choices=["-g", "-c"], help='"-g" to load from golden\n"-c" to chain from load_md')
#   parser.add_argument("action", choices=["-w", "-t", "-g"], help='"-w" to write test file\n"-t" to test output against golden\n"-g" to write output as golden')
#
# def main():
#   args = build_cli()
#   stage = STAGES[args.stage]
#   input = get_input(args.doc, args.stage, args.mode)
#   output = stage.opperation(args.doc, input)
#   if args.action == "-t":
#       result = stage.test_golden(args.doc, output)
#   else:
#       write_file(arg.doc, arg.stage, arg.mode, output)
