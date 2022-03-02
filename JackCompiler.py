from sys import argv
from pathlib import Path

from CompilationEngine import CompilationEngine
from JackTokenizer import JackTokenizer

class JackCompiler:
    def _getJackPaths():
        '''Returns a list of Path objects (the Jack files to compile) or None in the case of wrong program input'''
        if len(argv) != 2:
            print(f"Usage: {argv[0]} <single Jack file> | <directory with 0 or more Jack files>")
            return
        
        try:
            inputPath = Path(argv[1])
        except FileNotFoundError as error:
            print(error.strerror)
            return
        
        if inputPath.is_file():
            if not inputPath.as_posix().endswith(".jack"):
                print("Not a Jack file")
                return
            return [inputPath]
        elif inputPath.is_dir():
            return [file for file in inputPath.iterdir() if file.as_posix().endswith(".jack")]
        else:
            print("Not a jack file or directory")

    def main():
        jackInputPaths = JackCompiler._getJackPaths()
        if jackInputPaths is None:
            return

        for path in jackInputPaths:
            with open(path) as jackFile:
                tokenizer = JackTokenizer(jackFile)
                with open(Path(path.as_posix()[:-5] + ".vm"), "w") as vmFile:
                    engine = CompilationEngine(tokenizer, vmFile)
                    engine.compile()

if __name__ == "__main__":
    JackCompiler.main()