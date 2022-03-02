from asyncore import write
from re import S
from JackTokenizer import JackTokenizer
from io import TextIOBase

from SymbolTable import SymbolTable

class CompilationEngine:
    def __init__(self, tokenizer : JackTokenizer, vmFile : TextIOBase) -> None:
        self._tokenizer = tokenizer
        self._vmFile = vmFile
        self._symbolTable = SymbolTable()
        self._className = None
        self._labelCounter = 0
        self._opTranslations = {'+' : 'add', '-' : 'sub', '*' : 'call Math.multiply 2', '/' : 'call Math.divide 2', '&' : 'and', '|' : 'or', '<' : 'lt', '>' : 'gt', '=' : 'eq'}
    
    def compile(self) -> None:
        self._tokenizer.advance()
        self._compileClass()

    def _peekToken(self) -> str:
        return self._tokenizer.getToken()

    def _getTokenAndAdvance(self) -> str:
        token = self._peekToken()
        self._tokenizer.advance()
        return token

    def _eatToken(self, expectedToken : str) -> None:
        if self._peekToken() != expectedToken:
            raise SyntaxError(f"'{expectedToken}' expected, got '{self._peekToken()}'")
        self._tokenizer.advance()

    def _writeln(self, string : str) -> None:
        self._vmFile.write(f'{string}\n')
    
    '''
    Excpetion from the general rule: In the case "varName'.'subroutineName'('expressionList')'", the varName can be extracted from the tokenizer and pushed to the stack before this function is called, and and given to it a as a parameter. This is needed for part of the logic of _compileTerm().
    '''
    def _compileSubroutineCall(self, varName:str=None) -> None:
        if self._symbolTable.getType(self._peekToken()) is not None:
            varName = self._getTokenAndAdvance()
            self._writeln(f'push {self._symbolTable.translate(varName)}')

        if varName:
            self._eatToken('.')
            subroutineName = self._getTokenAndAdvance()
            self._eatToken('(')
            nrArgs = 1 + self._compileExpressionList()
            self._eatToken(')')
            self._writeln(f'call {self._symbolTable.getType(varName)}.{subroutineName} {nrArgs}')

        else: # function call or method call on the current object:
            name = self._getTokenAndAdvance()
            if self._peekToken() == '.': # function call:
                className = name
                self._eatToken('.')
                subroutineName = self._getTokenAndAdvance()
                self._eatToken('(')
                nrArgs = self._compileExpressionList()
                self._eatToken(')')
                self._writeln(f'call {className}.{subroutineName} {nrArgs}')
            else: # inclass method call
                subroutineName = name
                self._eatToken('(')
                self._writeln('push pointer 0') # Push this to the stack
                nrArgs = 1 + self._compileExpressionList()
                self._eatToken(')')
                self._writeln(f'call {self._className}.{subroutineName} {nrArgs}')

    def _compileClass(self) -> None:
        self._eatToken('class')
        self._className = self._getTokenAndAdvance()
        self._eatToken('{')
        while self._peekToken() in {'static', 'field'}:
            self._compileClassVarDec()
        while self._peekToken() in {'constructor', 'function', 'method'}:
            self._compileSubroutineDec()
        self._eatToken('}')

    def _compileClassVarDec(self) -> None:
        kind = self._getTokenAndAdvance()
        dataType = self._getTokenAndAdvance()
        
        while True:
            varName = self._getTokenAndAdvance()
            self._symbolTable.define(varName, dataType, kind)

            if self._peekToken() == ',':
                self._eatToken(',')
            else:
                break

        self._eatToken(';')

    def _compileSubroutineDec(self) -> None:
        self._symbolTable.startSubroutine()
        subroutineType = self._getTokenAndAdvance()
        if subroutineType == "method":
            self._symbolTable.define('this', self._className, 'argument')
        self._getTokenAndAdvance() # ignore the return type
        subroutineName = self._getTokenAndAdvance()
        self._eatToken('(')
        self._compileParameterList()
        self._eatToken(')')
        self._eatToken('{')

        localVariableCount = 0
        while self._peekToken() == 'var':
            self._eatToken('var')
            dataType = self._getTokenAndAdvance()
            while True:
                varName = self._getTokenAndAdvance()
                self._symbolTable.define(varName, dataType, 'local')
                localVariableCount += 1
                if self._peekToken() == ',':
                    self._eatToken(',')
                else:
                    break
            self._eatToken(';')

        self._writeln(f'function {self._className}.{subroutineName} {localVariableCount}')

        if subroutineType == 'constructor':
            objectSize = self._symbolTable.varCount('field')
            self._writeln(f'push constant {objectSize}')
            self._writeln('call Memory.alloc 1')
            self._writeln('pop pointer 0')
            
        elif subroutineType == 'method':
            self._writeln('push argument 0')
            self._writeln('pop pointer 0')
        
        self._compileStatements()
        self._eatToken('}')

    def _compileParameterList(self) -> None:
        if self._peekToken() != ')':
            while True:
                dataType = self._getTokenAndAdvance()
                varName = self._getTokenAndAdvance()
                self._symbolTable.define(varName, dataType, 'argument')
                if self._peekToken() == ',':
                    self._eatToken(',')
                else:
                    break

    def _compileStatements(self) -> None:
        while True:
            if self._peekToken() == 'let':
                self._compileLet()
            elif self._peekToken() == 'if':
                self._compileIf()
            elif self._peekToken() == 'while':
                self._compileWhile()
            elif self._peekToken() == 'do':
                self._compileDo()
            elif self._peekToken() == 'return':
                self._compileReturn()
            else:
                break

    def _compileLet(self) -> None:
        self._eatToken('let')
        varName = self._getTokenAndAdvance()
        if self._peekToken() == "[":
            self._writeln(f'push {self._symbolTable.translate(varName)}')
            self._eatToken('[')
            self._compileExpression()
            self._eatToken(']')
            self._eatToken('=')
            self._writeln('add')
            self._compileExpression()
            self._writeln('pop temp 0')
            self._writeln('pop pointer 1')
            self._writeln('push temp 0')
            self._writeln('pop that 0')
        else:
            self._eatToken('=')
            self._compileExpression()
            self._writeln(f'pop {self._symbolTable.translate(varName)}')
        
        self._eatToken(';')

    def _compileIf(self) -> None:
        labelCounter = self._labelCounter
        self._labelCounter += 1

        self._eatToken('if')
        self._eatToken('(')
        self._compileExpression()
        self._writeln('not')
        self._eatToken(')')
        self._writeln(f'if-goto {self._className}.IF_FALSE{labelCounter}')
        self._eatToken('{')
        self._compileStatements()
        self._eatToken('}')

        if self._peekToken() == 'else':
            self._writeln(f'goto {self._className}.END_IF{labelCounter}')
            self._writeln(f'label {self._className}.IF_FALSE{labelCounter}')

            self._eatToken('else')
            self._eatToken('{')
            self._compileStatements()
            self._eatToken('}')

            self._writeln(f'label {self._className}.END_IF{labelCounter}')
        else:
            self._writeln(f'label {self._className}.IF_FALSE{labelCounter}')

    def _compileWhile(self) -> None:
        labelCounter = self._labelCounter
        self._labelCounter += 1
        
        self._eatToken('while')
        self._eatToken('(')
        self._writeln(f'label {self._className}.BEGIN_WHILE{labelCounter}')
        self._compileExpression()
        self._writeln('not')
        self._writeln(f'if-goto {self._className}.END_WHILE{labelCounter}')
        self._eatToken(')')
        self._eatToken('{')
        self._compileStatements()
        self._eatToken('}')
        self._writeln(f'goto {self._className}.BEGIN_WHILE{labelCounter}')
        self._writeln(f'label {self._className}.END_WHILE{labelCounter}')

    def _compileDo(self) -> None:
        self._eatToken('do')
        self._compileSubroutineCall()
        self._eatToken(';')
        self._writeln('pop temp 0')

    def _compileReturn(self) -> None:
        self._eatToken('return')
        if self._peekToken() == ';':
            self._writeln('push constant 0')
        else:
            self._compileExpression()
        
        self._eatToken(';')
        self._writeln('return')

    def _compileExpression(self) -> None:
        self._compileTerm()
        while self._peekToken() in {'+', '-', '*', '/', '&', '|', '<', '>', '='}:
            opTranslation = self._opTranslations[self._getTokenAndAdvance()]
            self._compileTerm()
            self._writeln(opTranslation)
    
    def _compileTerm(self) -> None:
        if self._peekToken().isnumeric():
            self._writeln(f'push constant {self._getTokenAndAdvance()}')
        
        elif self._tokenizer.getTokenType() == 'stringConstant':
            string = self._getTokenAndAdvance()
            self._writeln(f'push constant {len(string)}')
            self._writeln('call String.new 1')
            for char in string:
                self._writeln(f'push constant {ord(char)}')
                self._writeln('call String.appendChar 2')
            
        elif self._peekToken() == 'true':
            self._eatToken('true')
            self._writeln('push constant 0')
            self._writeln('not')
        elif self._peekToken() == 'false':
            self._eatToken('false')
            self._writeln('push constant 0')
        elif self._peekToken() == 'null':
            self._eatToken('null')
            self._writeln('push constant 0')
        elif self._peekToken() == 'this':
            self._eatToken('this')
            self._writeln('push pointer 0')
        elif self._symbolTable.getType(self._peekToken()) is not None: # a variable
            varName = self._getTokenAndAdvance()
            self._writeln(f'push {self._symbolTable.translate(varName)}')
            if self._peekToken() == '[':
                self._eatToken('[')
                self._compileExpression()
                self._writeln('add')
                self._writeln('pop pointer 1')
                self._writeln('push that 0')
                self._eatToken(']')
            elif self._peekToken() == '.': # a method call on the variable
                self._compileSubroutineCall(varName)
                
        elif self._peekToken() == '(':
            self._eatToken('(')
            self._compileExpression()
            self._eatToken(')')
        elif self._peekToken() == '-':
            self._eatToken('-')
            self._compileTerm()
            self._writeln('neg')
        elif self._peekToken() == '~':
            self._eatToken('~')
            self._compileTerm()
            self._writeln('not')
        else:
            self._compileSubroutineCall()
    
    def _compileExpressionList(self) -> int: # Returns the length of the list 
        expressionCount = 0
        if self._peekToken() != ')':
            while True:
                self._compileExpression()
                expressionCount += 1
                if self._peekToken() == ',':
                    self._eatToken(',')
                else:
                    break
        return expressionCount