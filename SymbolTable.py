class SymbolTable:
    def __init__(self) -> None:
        self._classTable = {}
        self._classCounts = {'static' : 0, 'field' : 0}

    '''Starts a new subroutine's symbol table'''
    def startSubroutine(self) -> None:
        self._subroutineTable = {}
        self._subroutineCounts = {'argument' : 0, 'local' : 0}

    '''Defines a new identifier of the given name, type and kind and assigns it a running index.'''
    def define(self, name : str, dataType : str, kind : str) -> None:
        if kind in {'static', 'field'}:
            self._classTable[name] = (dataType, kind, self._classCounts[kind])
            self._classCounts[kind] += 1
        else:
            self._subroutineTable[name] = (dataType, kind, self._subroutineCounts[kind])
            self._subroutineCounts[kind] += 1

    '''Returns the number of variables of the given kind already defined in the current scope'''
    def varCount(self, kind : str) -> int:
        return self._classCounts[kind] if kind in {'static', 'field'} else self._subroutineCounts[kind]

    def _accessColumn(self, name : str, column : int) -> str:
        return self._classTable[name][column] if name in self._classTable else self._subroutineTable[name][column] if name in self._subroutineTable else None
    
    '''
    Returns the VM '<segment> <offset>' translation of the variable with the given name
    '''
    def translate(self, name : str) -> str:
        kind = self._accessColumn(name, 1)
        translatedKind = 'this' if kind == 'field' else kind
        return f'{translatedKind} {self._accessColumn(name, 2)}'
    
    '''
    Returns the type of the variable with the given name, or None if the variable is undefined
    '''
    def getType(self, name) -> str:
        return self._accessColumn(name, 0)
