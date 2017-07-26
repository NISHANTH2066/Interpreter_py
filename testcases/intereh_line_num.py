import sys
import re

memory={}
line_position=[]

#####################################
###############Lexer#################
#####################################

RESERVED='RESERVED'
INT='INT'
ID='ID'
PRINT='PRINT'
START='START'
END='END'
MIDDLE='MIDDLE'

token_exprs=[
    (r'[ \t]+',None),
    (r'[ \n]+',None),
    (r'#[^\n]*',None),
    (r'\(', RESERVED),
    (r'\)', RESERVED),
    (r'\:=',MIDDLE),
    (r';',  RESERVED),
    (r'\+', RESERVED),
    (r'-',  RESERVED),
    (r'\*', RESERVED),
    (r'/',  RESERVED),
    (r'<=', RESERVED),
    (r'<',  RESERVED),
    (r'>=', RESERVED),
    (r'>',  RESERVED),
    (r'=',  RESERVED),
    (r'!=', RESERVED),
    (r'and',RESERVED),
    (r'or', RESERVED),
    (r'not',RESERVED),
    (r'if', START),
    (r'fi', RESERVED),
    (r'then',RESERVED),
    (r'else',RESERVED),
    (r'while',START),
    (r'done', RESERVED),
    (r'do', RESERVED),
    (r'end',RESERVED),
    (r'println',START),
    (r'print',START),
    (r'\'[A-Za-z]*\'',PRINT),
    (r'[0-9]+',INT),
    (r'[A-Za-z][A-Za-z0-9_]*',ID),
]

def lex(characters,token_exprs):
    pos=0
    tokens=[]
    position=[]
    count=1
    while pos<len(characters):
        match=None
        for token_expr in token_exprs:
            pattern,tag=token_expr
            regex=re.compile(pattern)
            match=regex.match(characters,pos)
            if match:
                text=match.group(0)
                if tag:
                    token=(text,tag)
                    #print(token)
                    if tag==START:
                        if tokens[len(tokens)-1]!=';':
                            #print(tokens)
                            raise Exception('Syntax Error1 in line '+str(count-1))
                    elif tag==MIDDLE and count>1:
                        cur=tokens[len(tokens)-2]
                        if cur!='do' and cur!='then' and cur!=';' and cur!='else':
                            raise Exception('Syntax Error2 in line '+str(count-1))
                    tokens.append(text)
                    position.append(count)
                else:
                    #print(tokens)
                    #print(count)
                    #print(pattern)
                    if text=='\n':
                        #print(tokens)
                        #print(count)
                        count+=1
                	#print(count)
                break
        if not match:
            sys.stderr.write('Illegal character: %s in line %d\n'%(characters[pos],count))
            sys.exit(1)
        else:
            pos=match.end(0)
    global line_position
    line_position=position
    #print(line_position[:],"Lexer")
    return tokens


#####################################
###############Program###############
#####################################

class Program(object):
    def __init__(self,tokens):
        #print(line_position[:],"Program")
        self.program = CompoundStatement(tokens,line_position)

    def eval(self):
        self.program.eval()

    def __repr__(self):
        return str(self.program)

class CompoundStatement(object):
    def __init__(self,tokens,line_position):
        self.tokens = tokens
        self.statements = []
        self.line_position=line_position
        #print(line_position[:],"Compound")
        pos = 0
        while pos<len(tokens):
            s = tokens[pos]
            if tokens[pos] =='while':
                temp_pos=pos
                count,pos=1,pos+1
                dopos=0
                docount=0
                while count>0:
                    if tokens[pos]=='do' and docount==0:
                        #print(tokens[pos:])
                        dopos=pos
                        docount=1
                    if tokens[pos]=='while':
                        count+=1
                    elif tokens[pos]=='done':
                        count-=1
                    pos+=1
                s=WhileStatement(tokens[temp_pos:pos],dopos-temp_pos,line_position[temp_pos:pos])
                pos+=1
            elif tokens[pos] == 'if':
                temp_pos=pos
                count,pos=1,pos+1
                thencount,thenpos=0,0
                while count>0:
                    if tokens[pos]=='then' and thencount==0:
                        thenpos=pos
                        thencount=1
                    if tokens[pos]=='if':
                        count+=1
                    elif tokens[pos]=='fi':
                        count-=1
                    pos+=1
                s= IfCondition(tokens[temp_pos:pos],thenpos-temp_pos,line_position[temp_pos:pos])
                pos+=1
            elif tokens[pos]=='print' or tokens[pos]=='println':
                temp_pos=pos
                #print(tokens[pos:])
                while tokens[pos]!=';' and tokens[pos]!='end':
                    pos+=1
                s= PrintStatement(tokens[temp_pos:pos],line_position[temp_pos:pos])
                pos+=1
            else:
                #print(tokens[pos:])
                temp_pos=pos
                while(tokens[pos]!=';' and tokens[pos]!='end'):
                    pos+=1
                #print(line_position[temp_pos:pos])
                s = Statement.build(tokens[temp_pos:pos],line_position[temp_pos:pos])
                pos+=1        
            self.statements.append(s)

    def eval(self):
        for s in self.statements:
            #print(type(s),s)
            # if isinstance(s,AssignmentStatement):
            #     print('Yeah')
            s.eval()

    def __repr__(self):
        temp=''
        for s in self.statements:
            temp+=str(s)+' \n'
        temp=temp[:-1]
        return 'CompoundStatement('+ temp +')'

class Statement(object):
    def __init__(self,s):
        self.statement=s
        if ':=' in s:
            self.statement=AssignmentStatement(s)

    def build(s,line_position):
        if ':=' in s:
            #print(line_position,"SBuild")
            return AssignmentStatement(s,line_position)

    def eval(self):
        print('\n',self.statement,'\n')
        self.statement.eval()

    def __repr__(self):
        return str(self.statement)

class AssignmentStatement(object):
    def __init__(self,s,line_position):
        self.name=s[0]
        #print(line_position,"Assign")
        self.expr=Expression.build(s[2:],line_position[2:])
        self.lpos=line_position[0]

    def eval(self):
        memory[self.name]=self.expr.eval()

    def __repr__(self):
        return 'AssignmentStatement(%s, %s)' % (self.name, self.expr)

class IfCondition(object):
    def __init__(self,s,thenpos,line_position):
        pos=thenpos
        # while s[pos]!='then':
        #     pos+=1
        self.lpos=line_position[0]
        self.condition=ConditionalExpression.build(s[1:pos],line_position[1:pos])
        if 'else' not in s[pos:]:
            self.truesatements=CompoundStatement(s[pos+1:len(s)-1]+['end'],line_position[pos+1:len(s)])
            self.falsestatements=None
        else:
            s=s[pos:]
            pos=1
            while s[pos]!='else':
                pos+=1
            self.truesatements=CompoundStatement(s[1:pos]+['end'],line_position[1:pos+1])
            self.falsestatements=CompoundStatement(s[pos+1:len(s)-1]+['end'],line_position[pos+1:len(s)])

    def eval(self):
        if self.condition.eval():
            self.truesatements.eval()
        else:
            if self.falsestatements:
                self.falsestatements.eval()

    def __repr__(self):
        return 'IfCondition(%s, %s,%s)' % (self.condition, \
            self.truesatements,self.falsestatements)

class WhileStatement(object):
    def __init__(self,s,dopos,line_position):
        #print(s)
        pos=dopos
        lpos=line_position[0]
        # while s[pos]!='do':
        #     pos+=1
        self.condition=ConditionalExpression.build(s[1:pos],line_position[1:pos])
        self.statements=CompoundStatement(s[pos+1:len(s)-1]+['end'],line_position[pos+1:len(s)])

    def eval(self):
        while self.condition.eval():
            self.statements.eval()

    def __repr__(self):
        return 'WhileLoop(%s, %s)' % (self.condition, self.statements)


class PrintStatement(object):
    def __init__(self,tokens,lpos):
        #print(tokens)
        self.lpos=lpos[0]
        if tokens[0]=='println':
            self.s=StringExpression('',lpos[:1])
        else:
            self.s=Expression.build(tokens[1],lpos)

    def eval(self):
        #print(self.s)
        print(self.s.eval())

    def __repr__(self):
        return 'PrintStatement(%s)' % (self.s)

#################################
###########Expression############
#################################

class Expression:
    def build(s,lpos):
        if type(s)==list and not s:
            return ConstantExpression('0',lpos)
        #print(s,"AAAAAAAAAA")
        #print(s)
        #print(s,lpos,"LLLLL")
        if s[0]=='(' and s[len(s)-1]==')' and '(' not in s[1:-1]:
            return Expression.build(s[1:-1],lpos[1:-1])
        # p,count=1,1
        # if s[0]=='(':
        #     t=['(']
        #     while count!=0:
        #         if s[p]=='(':
        #             count+=1
        #         elif s[p]==')':
        #             count-=1
        #         t.append(s[p])
        #         p+=1
        p,count=0,0
        while p<len(s):
            if s[p]=='(':
                count+=1
            elif s[p]==')':
                count-=1
            if count==0:
                l=s[:p]
                #print(s,lpos,"Expression")
                lposl=lpos[:p]
                if s[p]=='+':
                    if s[0]=='(' and s[p-1]==')':
                        #s[:p]=s[1:p-1]
                        l=s[1:p-1]
                        lposl=lpos[1:p-1]
                    return AdditionExpression(l,s[p+1:],lposl,lpos[p+1:])
                elif s[p]=='-':
                    if s[0]=='(' and s[p-1]==')':
                        l=s[1:p-1]
                        lposl=lpos[1:p-1]
                    return SubtractionExpression(l,s[p+1:],lposl,lpos[p+1:])
                elif s[p]=='*':
                    if s[0]=='(' and s[p-1]==')':
                        l=s[1:p-1]
                        lposl=lpos[1:p-1]
                    return MultiplicationExpression(l,s[p+1:],lposl,lpos[p+1:])
                elif s[p]=='/':
                    if s[0]=='(' and s[p-1]==')':
                        l=s[1:p-1]
                        lposl=lpos[1:p-1]
                    return DivisionExpression(l,s[p+1:],lposl,lpos[p+1:])
            p+=1
        #print(s,"Expression")
        if s[0]=='"' or s[0][0]=="'" or s[0]=="'":
            print(s,"Expression")
            return StringExpression(s,lpos)
        elif s[0].isalpha():
            return VariableExpression(s,lpos)
        else:
            #print(s,lpos,"Expression")
            return ConstantExpression(s,lpos)

class AdditionExpression(object):
    def __init__(self,l,r,lposleft,lpos):
        self.left,self.right=l,r
        self.left=Expression.build(self.left,lposleft)
        self.right=Expression.build(self.right,lpos)
        self.lpos=lpos[0]

    def eval(self):
        return self.left.eval()+self.right.eval()

    def __repr__(self):
        return 'AdditionExpression(%s, %s)' % (self.left, self.right)

class SubtractionExpression(object):
    def __init__(self,l,r,lposleft,lpos):
        self.left,self.right=l,r
        if not lposleft:
        	lposleft=lpos[:1]
        self.left=Expression.build(self.left,lposleft)
        self.right=Expression.build(self.right,lpos)
        self.lpos=lpos[0]

    def eval(self):
        return self.left.eval()-self.right.eval()

    def __repr__(self):
        return 'SubtractionExpression(%s, %s)' % (self.left, self.right)

class MultiplicationExpression(object):
    def __init__(self,l,r,lposleft,lpos):
        self.left,self.right=l,r
        self.left=Expression.build(self.left,lposleft)
        self.right=Expression.build(self.right,lpos)
        self.lpos=lpos[0]

    def eval(self):
        return self.left.eval()*self.right.eval()

    def __repr__(self):
        return 'MultiplicationExpression(%s, %s)' % (self.left, self.right)

class DivisionExpression(object):
    def __init__(self,l,r,lposleft,lpos):
        self.left,self.right=l,r
        self.left=Expression.build(self.left,lposleft)
        self.right=Expression.build(self.right,lpos)
        self.lpos=lpos[0]

    def eval(self):
        right=self.right.eval()
        if right==0:
            raise ZeroDivisionError('Division by zero error in line '+str(self.lpos))
        return self.left.eval()/right

    def __repr__(self):
        return 'DivisionExpression(%s, %s)' % (self.left, self.right)

class VariableExpression(object):
    def __init__(self,s,lpos):
        self.name=s[0]
        self.lpos=lpos[0]

    def __repr__(self):
        return 'VariableExpression(%s)' % self.name

    def eval(self):
        if self.name in memory:
            return memory[self.name]
        else:
            return 0

class ConstantExpression(object):
    def __init__(self, s,lpos):
        #print(s)
        self.i = int(s[0])
        #print(lpos)
        self.lpos=lpos[0]

    def __repr__(self):
        return 'ConstantExpression(%d)' % self.i

    def eval(self):
        return self.i

class StringExpression(object):
    def __init__(self, s,lpos):
        #print(s)
        self.i = s
        self.lpos=lpos[0]

    def __repr__(self):
        return 'StringtExpression(%s)' % self.i

    def eval(self):
        return self.i

#######################################
########ConditionalExpression##########        
#######################################

class ConditionalExpression:
    def build(s,lpos):
        #print(s)
        if 'and' in s or 'or' in s:
            if s[0]=='(' and s[len(s)-1]==')' and '(' not in s[1:-1]:
                return ConditionalExpression.build(s[1:-1],lpos[1:-1])
            p,count=0,0
            while p<len(s):
                if s[p]=='(':
                    count+=1
                elif s[p]==')':
                    count-=1
                if count==0:
                    l=s[:p]
                    lposl=lpos[:p]
                    if s[p]=='and':
                        if s[0]=='(' and s[p-1]==')':
                            #s[:p]=s[1:p-1]
                            l=s[1:p-1]
                            lposl=lpos[1:p-1]
                        return AndExp(l,s[p+1:],lposl,lpos[p+1:])
                    elif s[p]=='or':
                        if s[0]=='(' and s[p-1]==')':
                            l=s[1:p-1]
                            lposl=lpos[1:p-1]
                        return OrExp(l,s[p+1:],lposl,lpos[p+1:])
                p+=1
        pos=0
        conditions = ['<', '<=', '>', '>=', '=', '!=']
        while s[pos] not in conditions:
            pos+=1
        l=s[:pos]
        lposl=s[:pos]
        r=s[pos+1:]
        lposr=s[pos+1:]
        if s[pos]=='<':
            return LessthanExpr(l,r,lposl,lposr)
        elif s[pos]=='<=':
            return LessthanEqualExpr(l,r,lposl,lposr)
        elif s[pos]=='>':
            return GreaterthanExpr(l,r,lposl,lposr)
        elif s[pos]=='>=':
            return GreaterthanEqualExpr(l,r,lposl,lposr)
        elif s[pos]=='=':
            return EqualExpr(l,r,lposl,lposr)
        elif s[pos]=='!=':
            return NotEqualExpr(l,r,lposl,lposr)

class LessthanExpr(object):
    def __init__(self,l,r,lposl,lposr):
        self.left=Expression.build(l,lposl)
        self.right=Expression.build(r,lposr)

    def eval(self):
        if self.left.eval()<self.right.eval():
            return True
        else:
            return False

    def __repr__(self):
        return 'LessthanExpr(%s, %s)' % (self.left, self.right)

class LessthanEqualExpr(object):
    def __init__(self,l,r,lposl,lposr):
        self.left=Expression.build(l,lposl)
        self.right=Expression.build(r,lposr)

    def eval(self):
        if self.left.eval()<=self.right.eval():
            return True
        else:
            return False

    def __repr__(self):
        return 'LessthanEqualExpr(%s, %s)' % (self.left, self.right)

class GreaterthanExpr(object):
    def __init__(self,l,r,lposl,lposr):
        self.left=Expression.build(l,lposl)
        self.right=Expression.build(r,lposr)

    def eval(self):
        if self.left.eval()>self.right.eval():
            return True
        else:
            return False

    def __repr__(self):
        return 'GreaterthanExpr(%s, %s)' % (self.left, self.right)

class GreaterthanEqualExpr(object):
    def __init__(self,l,r,lposl,lposr):
        self.left=Expression.build(l,lposl)
        self.right=Expression.build(r,lposr)

    def eval(self):
        if self.left.eval()>=self.right.eval():
            return True
        else:
            return False

    def __repr__(self):
        return 'GreaterthanEqualExpr(%s, %s)' % (self.left, self.right)

class EqualExpr(object):
    def __init__(self,l,r,lposl,lposr):
        self.left=Expression.build(l,lposl)
        self.right=Expression.build(r,lposr)

    def eval(self):
        if self.left.eval()==self.right.eval():
            return True
        else:
            return False

    def __repr__(self):
        return 'EqualExpr(%s, %s)' % (self.left, self.right)

class NotEqualExpr(object):
    def __init__(self,l,r,lposl,lposr):
        self.left=Expression.build(l,lposl)
        self.right=Expression.build(r,lposr)

    def eval(self):
        if self.left.eval()!=self.right.eval():
            return True
        else:
            return False

    def __repr__(self):
        return 'NotEqualExpr(%s, %s)' % (self.left, self.right)

class AndExp(object):
    def __init__(self, left, right,lposl,lposr):
        self.left = ConditionalExpression.build(left,lposl)
        self.right = ConditionalExpression.build(right,lposr)

    def __repr__(self):
        return 'AndExp(%s, %s)' % (self.left, self.right)

    def eval(self):
        left_value = self.left.eval()
        right_value = self.right.eval()
        return left_value and right_value

class OrExp(object):
    def __init__(self, left, right,lposl,lposr):
        self.left = ConditionalExpression.build(left,lposl)
        self.right = ConditionalExpression.build(right,lposr)

    def __repr__(self):
        return 'OrExp(%s, %s)' % (self.left, self.right)

    def eval(self):
        left_value = self.left.eval()
        right_value = self.right.eval()
        return left_value or right_value

################################
#############Main###############
################################

if __name__=='__main__':
    if len(sys.argv) != 2:
        print('Filename not given')
        sys.argv.append('myprog.txt')
    filename = sys.argv[1]
    text = open(filename).read()
    tokens = lex(text,token_exprs)
    print(tokens)
    program=Program(tokens)
    print(program)
    program.eval()
    print(memory)
    # if not parse_result:
    #     sys.stderr.write('Parse error!\n')
    #     sys.exit(1)
    # ast = parse_result.value
    # env = {}
    # ast.eval(env)

    # sys.stdout.write('Final variable values:\n')
    # for name in env:
    #     sys.stdout.write('%s: %s\n' % (name, env[name]))