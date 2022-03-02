from io import TextIOBase

class JackTokenizer:
    def __init__(self, jackFile : TextIOBase) -> None:
        self._jackFile = jackFile
        self._currentToken = ""
        self._currentLine = ""
        self._currentTokenType = ""

    def hasMoreTokens(self) -> bool:
        return self._currentToken is not None

    def advance(self) -> None:
        while True:
            if self._currentLine == "": # If the current line has been fully processed
                self._currentLine = self._jackFile.readline()
                if self._currentLine == "": # If the end of file was reached
                    self._currentToken = None
                    return
            
            self._currentLine = self._currentLine.strip() # Remove leading whitespace
            if self._currentLine == "": # If the stripping emptied the line:
                continue

            if self._currentLine[0] == '/' and len(self._currentLine) >= 2: # Handle comments first
                if self._currentLine[1] == '/': # a '//' comment
                    self._currentLine = "" # Delete the comment
                    continue
                if self._currentLine[1] == '*': # a block comment
                    endOfComment = self._currentLine.find("*/")
                    while endOfComment == -1: # While the comment's end is not in the current line:
                        self._currentLine = self._jackFile.readline()
                        if self._currentLine == "": # If the end of file was reached inside a block comment
                            raise SyntaxError("Expected */ before end of file")
                        endOfComment = self._currentLine.find("*/")
                    
                    self._currentLine = self._currentLine[endOfComment + 2 :] # Remove the block comment from the beginning of the line
                    continue
            
            # If the line did not begin with a comment:
            if self._currentLine[0] in {'{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/', '&', '|', '<', '>', '=', '~'}:
                self._currentToken =  self._currentLine[0]
                self._currentTokenType = "symbol"
                self._currentLine = self._currentLine[1:]
                return
            if self._currentLine[0] == '"':
                stringEnd = self._currentLine.find("\"", 1)
                self._currentToken = self._currentLine[1:stringEnd]
                self._currentTokenType = "stringConstant"
                self._currentLine = self._currentLine[stringEnd + 1 :]
                return
            if self._currentLine[0].isnumeric():
                index = 1
                while index < len(self._currentLine) and self._currentLine[index].isnumeric():
                    index += 1
                self._currentToken = self._currentLine[:index]
                self._currentTokenType = "integerConstant"
                self._currentLine = self._currentLine[index:]
                return
            if self._currentLine[0].isalpha() or self._currentLine[0] == '_':
                index = 1
                while index < len(self._currentLine) and (self._currentLine[index].isalnum() or self._currentLine[0] == '_'):
                    index += 1
                word = self._currentLine[:index]
                self._currentToken = word
                self._currentLine = self._currentLine[index:]
                self._currentTokenType = "keyword" if word in {'class', 'constructor', 'function', 'method', 'field', 'static', 'var', 'int', 'char', 'boolean', 'void', 'true', 'false', 'null', 'this', 'let', 'do', 'if', 'else', 'while', 'return'} else "identifier"
                return
    
    def getTokenType(self) -> str:
        return self._currentTokenType
    
    def getToken(self) -> str:
        return self._currentToken