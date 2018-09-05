#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Support functions for handling tokens. Now in class form.
"""
# debug :-(
from sys import stderr

from .analysis import Analysis


class Token:
    """Token holds a slice of text with its analyses and features.

    Token is typically a word-form, such as "pojat" or "juopottelevat", but
    can also be a white-space sequence or placeholder for some out of text
    metadata, a tag, comment or i/o error.

    For a reference, see [spaCy tokens](https://spacy.io/api/token), it's
    not exactly the same thing and I don't agree with all there, but it's
    quite cool and well-documented.
    """

    def __init__(self, surf=None):
        """Create token with surface string optionally."""
        ## underlying raw omor analysis
        self.analyses = []
        ## original surface form
        self.surf = surf
        ## word index in context, e.g. UD column 1
        self.pos = 0
        ## nontoken
        self.nontoken = False
        ## comment (esp. with non-token)
        self.comment = None
        ## use when tokenisation or parsing breaks
        self.error = None
        ## If token is separated by space from left
        self.spacebefore = False
        ## If token is separated by space from right
        self.spaceafter = False

    def __getitem__(self, key):
        """Tokens can still be accessed like dicts for compatibility.

        Some keys like surf and pos are obvious and direct while some old keys
        like omor for analysis is mapped to 1-random analysis string if there
        are any.
        """
        if key == 'anal':
            # return first omor analysis for b/w comp & ease of use
            for analysis in self.analyses:

                if analysis.name == 'omor':
                    return analysis.raw
            return None
        elif key == 'surf':
            return self.surf
        elif key == 'pos':
            return self.pos
        else:
            raise KeyError(key)

    def __str__(self):
        s = '"omorfi.Token": {'
        if self.surf:
            s += '"surf": "' + self.surf + '"'
        if self.nontoken:
            s += '"nontoken": "' + self.nontoken + '"'
        if self.pos:
            s += ',\n "pos": "' + str(self.pos) + '"'
        if self.analyses:
            s += ',\n "omorfi.Analyses": [\n'
            s += ',\n '.join(self.analyses)
            s += '\n]'
        if self.error:
            s += ',\n "error": "' + self.error + '"'
        if self.comment:
            s += ',\n "comment": "' + self.comment + '"'
        s += '}'
        return s

    @staticmethod
    def fromstr(s: str):
        """Creates token from string.

        Strings should be made with print(token).
        """
        lines = s.split("\n")
        token = Token()
        in_anals = False
        for line in lines:
            if '"omorfi.Token"' in line:
                # first
                continue
            elif line.strip() == '}':
                # last
                continue
            elif in_anals:
                if line.strip() == ']':
                    in_anals = False
                else:
                    anal = Analysis.fromstr(line)
                    token.analyses.append(anal)
            else:
                k, v = line.split(":")
                if k == '"surf"':
                    token.surf = v.strip().strip('"')
                elif k == '"nontoken"':
                    token.nontoken = v.strip().strip('"')
                elif k == '"pos"':
                    token.pos = int(v.strip().strip('"'))
                elif k == '"error"':
                    token.error = v.strip().strip('"')
                elif k == '"comment"':
                    token.comment = v.strip().strip('"')
                elif k == '"omorfi.Analyses"':
                    in_anals = True
                else:
                    print("Error parsing token", line, file=stderr)
                    exit(1)
        return token

    @staticmethod
    def fromdict(token: dict):
        """Create token from pre-2019 tokendict."""
        cons = Token(token['surf'])
        for k, v in token.items():
            if k == 'anal':
                anal = Analysis(v, 0.0)
                cons.analyses.append(anal)
        return cons

    @staticmethod
    def fromsurf(surf: str):
        """Creat token from surface string."""
        return Token(surf)

    @staticmethod
    def fromconllu(conllu: str):
        """Create token from conll-u line."""
        fields = conllu.split()
        if len(fields) != 10:
            print("conllu2token conllu fail", fields)
        upos = fields[3]
        wordid = fields[2]
        surf = fields[1]
        ufeats = fields[5]
        misc = fields[9]
        omor = Analysis('[WORD_ID=' + wordid + ']' + '[UPOS=' + upos + ']' +
                        Token._ufeats2omor(ufeats), 0.0, "omor")
        omor.misc = misc
        token = Token(surf)
        token.analyses.append(omor)
        # we can now store the original here
        orig = Analysis(conllu, 0.0, "conllu")
        token.analyses.append(orig)
        token.surf = surf
        return token

    @staticmethod
    def fromvislcg(s: str):
        '''Create a token from VISL CG-3 text block.

        The content should at most contain one surface form with a set of
        analyses.
        '''
        token = Token()
        lines = s.split('\n')
        for line in lines:
            line = line.rstrip()
            if not line or line == '':
                token.nontoken = 'separator'
            elif line.startswith("#") or line.startswith("<"):
                token.nontoken = 'comment'
                token.comment = line.strip()
            elif line.startswith('"<') and line.endswith('>"'):
                token.surf = line[2:-2]
            elif line.startswith('\t"'):
                anal = Analysis(line.strip(), 0.0, "vislcg")
                token.analyses.append(anal)
            elif line.startswith(';\t"'):
                # gold?
                anal = Analysis(line[1:].strip(), float("inf"), "vislcg")
                token.analyses.append()
            else:
                token.nontoken = "error"
                token.error = 'vislcg: ' + line.strip()
        return token

    @staticmethod
    def _ufeats2omor(ufeats):
        return '[' + ufeats.replace('|', '][') + ']'

    def is_oov(self):
        '''Checks if all hypotheses are OOV guesses.'''
        for analysis in self.analyses:
            if not analysis.is_oov():
                return False
        return True

    def printable_vislcg(self):
        '''Create VISL-CG 3 output based on token and its analyses.'''
        vislcg = '"<' + self.surf + '>"\n'
        for anal in self.analyses:
            vislcg += anal.printable_vislcg()
        return vislcg
