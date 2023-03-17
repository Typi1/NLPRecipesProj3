from enum import Enum
from typing import Optional
import stanza as st

ingredient_labels = ["ingredient", "slices", "chunks", "quantity"]
tool_labels = ["appliance", "cooking utensil", "container", "bowl", "pan", "board", "measuring tool", "knife", "strainer", "colinder", "spatula"]
separation_labels = ["separate", "remove", "sift", "drain", "disgard", "filter"]
combination_labels = ["add", "combine", "mix", "stir", "blend", "pour"]


class ListType(Enum):
    AND = 0 # a list of things that all are required
    OR = 1 # a list of things that can be substituted
    UNSPECIFIED = 2 # if the list type cannot be determined

# represents combinations of ingredients like a batter being made of eggs and stuff. uses list detection and dependency parsers to form this
class IngredCombo:
    def __init__(   self, 
                    id: int,            # a unique id for each ingredient combo object 
                    grouping_verb: str, # the verb that applies to the combination of ingredients. ex: "mix", "place X in bowl"/"stir"
                    constituents: list, # list of strings that go into this combination
                    combo_names: Optional[list] = None):
        self.id = id
        self.grouping_verb = grouping_verb
        self.constituents = constituents
        self.combo_names = []
        if combo_names != None:
            self.combo_names += combo_names

    def addComboName(self, name:str):
        self.combo_names.append(name)
    
    def makeList(self):
        test_str = ""
        for x in self.constituents:
            test_str += x
            test_str += " "
        return test_str.rstrip()
    
    # TODO
    def addConstituent(self, ingr):
        pass

    def __str__(self):
        return "Combination type: " + self.combo_type + "\n\tGrouping verb: " + self.grouping_verb + "\n\tConstituents: " + str(self.constituents)


# note when going over ingredients, if there is a verb associated with it (like chopped leeks), make it a step if not already (chop leeks)

class Step:
    def __init__(   self, 
                    id: int = 0, # the number of the step
                    root_action: str = "", # the root verb of the step
                    actions: dict = None, 
                    ingredients: dict = None, # the ingredients required as keys (num/amount [count/mass] and list of qualifiers [adjs] as value)
                        # could also use some ingredient ID instead of using a list of qualifiers on the ingredient [the class referred to by the ID]
                    tools: dict = None, # the tools and/or appliances and/or pots/pans/bowls required
                    details: dict = None, # adverbs and descriptors. key is a numerical ID. value is DetailType enum and substring
                    original_text: str = ""): 
        self.root_action = root_action
        self.actions = {}
        if actions != None:
            self.actions = actions
        self.ingredients = {}
        if ingredients != None:
            self.ingredients = ingredients
        self.tools = {}
        if tools != None:
            self.tools = tools
        self.details = {}
        if details != None:
            self.details = details
        self.id = id 
        self.original_text = original_text



    def __str__(self):
        outputStr = ""
        outputStr = outputStr +  "id: " + str(self.id)
        outputStr = outputStr + "\nOriginal text: " + str(self.original_text)
        outputStr = outputStr + "\n\tRoot action: " + str(self.root_action)
        outputStr = outputStr + "\n\tAll actions: " + str(self.actions)
        outputStr = outputStr + "\n\tIngredients: " + str(self.ingredients)
        outputStr = outputStr + "\n\tTools: " + str(self.tools)
        outputStr = outputStr + "\n\tDetails: " + str(self.details)
        return outputStr
    
# if head_id is -1 or id is 0, this is the root node
class depNode():
    def __init__(self, id:int, head_id:int, text:str, typ: str, deps:dict):
        self.id = id
        self.head_id = head_id
        self.text = text
        self.typ = typ
        self.deps = deps
        if deps == None:
            self.deps = {}

    def addDependent(self, dep_id:int, dep_text:str, rel_type:str):
        if dep_id in self.deps.keys():
            return
        self.deps[dep_id] = (dep_id, dep_text, rel_type)

    def __str__(self):
        outputStr = ""
        outputStr += "ID: " + str(self.id)
        outputStr += "\n\tHead ID: " + str(self.head_id)
        outputStr += "\n\tText: " + self.text
        outputStr += "\n\tType: " + self.typ
        outputStr += "\n\tDependent Words: "
        for x in self.deps.keys():
            outputStr += "\n\t\tDep. ID: " + str(self.deps[x][0])
            outputStr += "\n\t\t\tDep. Text: " + self.deps[x][1]
            outputStr += "\n\t\t\tRelation Type: " + self.deps[x][2]
        return outputStr
            

# returns a easier to traverse dependency tree with word id in the sentence as the key, as well as a dictionary of a word to a list of ids of instances of it
def getDependency(input_dep:list):
    text_to_ids = {} # ex: For the sentence, "cakes are cakes": text_to_ids["cakes"] == [1,3] 
    dependency_dict = {}

    # add a special node for ROOT
    dependency_dict[0] = depNode(0, -1, "ROOT", "N/A", {})

    for entry in input_dep:

        id1 = entry[0].id
        txt1 = entry[0].text.lower()
        id2 = entry[2].id
        txt2 = entry[2].text.lower()
        rel_type = entry[1]

        # if either word id isn't in the dependency dictionary, add it
        if not id1 in dependency_dict.keys():
            dependency_dict[id1] = depNode(id1, entry[0].head, txt1, entry[0].xpos, {})
            if not txt1 in text_to_ids.keys():
                text_to_ids[txt1] = [id1]
            elif txt1 in text_to_ids.keys() and not id1 in text_to_ids[txt1]:
                text_to_ids[txt1] = text_to_ids[txt1] + [id1]

        if not id2 in dependency_dict.keys():
            dependency_dict[id2] = depNode(id2, entry[2].head, txt2, entry[2].xpos, {})
            if not txt2 in text_to_ids.keys():
                text_to_ids[txt2] = [id2]
            elif txt2 in text_to_ids.keys() and not id2 in text_to_ids[txt2]:
                text_to_ids[txt2] = text_to_ids[txt2] + [id2]

        # add a dependency into the head word
        dependency_dict[id1].addDependent(id2, txt2, rel_type)

    return (dependency_dict, text_to_ids)
        
        

# returns whether the input word is an appliance, utensil, measuring tool, etc.
# return is bool of whether tool or not, and (updated) seen dict
def isTool(pipe2, text:str, seen:dict):
    res = False
    text = text.lower()
    if not text in seen.keys():
        (_, seen) = getNounType(pipe2, text, seen)
        # print("?")

    if (text in seen.keys()) and seen[text]['labels'][0] in tool_labels:
            if seen[text]['scores'][0] > 0.1:
                res = True

    return (res, seen)

def isIngredient(pipe2, text:str, seen:dict):
    res = False
    text = text.lower()
    if not text in seen:
        (_, seen) = getNounType(pipe2, text, seen)
        # print("?")

    if (text in seen) and seen[text]['labels'][0] in ingredient_labels:
            res = True

    return (res, seen)



def getNounType(pipe2, text:str, seen: dict):
    res = ""
    text = text.lower()
    if text in seen:
        res = seen[text]
    else:
        # add something here which will check if the noun is in the ingredients list
        lst = ["time"] + ingredient_labels + tool_labels
        res = pipe2(text, candidate_labels=lst)
        seen[text] = res

    # print(res)
    # print(seen)
    return (res['labels'][0], seen)

def getAdjType(pipe2, text:str, seen: dict):
    res = ""
    if text in seen:
        res = seen[text]
    else:
        res = pipe2(text, candidate_labels=["preparation manner", "compliment", "color", "texture", "temperature", "viscosity", "taste", "size"])
        seen[text] = res
    
    return (res['labels'][0], seen)

def getFirstType(children:list, typ: str):
    res = None
    for branch in children:
        if branch.label == typ:
            return branch
        else:
            res = getFirstType(branch.children, typ)
            if res != None and res.label == typ:
                return res
            
    return res

# same as above function, but uses "in" to make it so the general category of word is easier to get. 
# for example, if we are looking for a noun, we would have to find NN, NNS, NNP, NNPS, etc. with the above function.
# With this more broad function, just searching with type NN would get all of those/
def getFirstTypeBroad(children:list, typ: str):
    res = None
    for branch in children:
        if typ in branch.label:
            return branch
        else:
            res = getFirstTypeBroad(branch.children, typ)
            if res != None and typ in res.label:
                return res
            
    return res
            
def getAllOfTypes(children:list, typs: list):
    res = []

    if len(children) == 1 and children[0].label == str(children[0]):
        return res
    
    for branch in children:
        if "NN" in typs and branch.label == "VP": continue
        if any(branch.label == typ for typ in typs):
            if len(branch.children) == 1 and branch.children[0].label == str(branch.children[0]):
                res.append(branch.children[0].label)
            else:
                res.append(constituency_to_str(branch))
        # special case for collecting compound nouns 
        elif "NN" in typs and branch.label == "NP" and isComboNounPhrase(branch):
            res.append(constituency_to_str(branch))
        else:
            temp = getAllOfTypes(branch.children, typs)
            if temp != []:
                res += temp # res.append(temp)

    return res

def stepsToPara(steps:list):
    res = ""
    for x in steps:
        res += str(x) + " "

    return res.rstrip()
        
def getWordsRecurs(children:list, words:list):
    for branch in children:
        if(branch.label == str(branch)):
            words.append(branch.label)
            continue
        words = getWordsRecurs(branch.children, words)

    return words

def constituency_to_str(tree:st.models.constituency.parse_tree.Tree):
    children = tree.children
    words = []
    # do a Depth First Traversal and add words to the list
    words = getWordsRecurs(children, words)

    res = ""

    for x in words:
        if x == "." or x == "," or x == "'" or x == ";" or x == ":" or x == "-" or x == "/":
            res = res.rstrip()
        res += x
        res += " "

    return res.rstrip()

# determines whether a noun phrase NP is a combination of nouns (ex: "the confectioners' sugar" or "the lemon zest")
def isComboNounPhrase(tree:st.models.constituency.parse_tree.Tree):
    children = tree.children
    return all(not child.label in [",",".",";","CC","VP","VB"] for child in children)


def getAllDepTuples(dependencies:dict, curr_id:int):
    res = [(curr_id, dependencies[curr_id].text)]
    for dp in dependencies[curr_id].deps:
        res += getAllDepTuples(dependencies, dependencies[curr_id].deps[dp][0])
    return res

# returns the phrase that the string of curr_id is in based on dependencies
def getDepPhrase(dependencies:dict, curr_id:int):
    # first, get all the dependent tuple data using DFS
    tuples = getAllDepTuples(dependencies, curr_id)
    # now order them into a phrase string
    tuples.sort(key=(lambda x: x[0]), reverse=False)
    res = ""
    for t in tuples:
        if t[1] == "." or t[1] == "," or t[1] == "'" or t[1] == ";" or t[1] == ":" or t[1] == "-" or t[1] == "/":
            res = res.rstrip()
        res += t[1]
        res += " "

    return res.rstrip()

# gets the head verb for a noun
def getHeadVerb(dependencies:dict, curr_id:int):

    head = dependencies[curr_id].head_id

    # if we somehow get to the root without seeing a verb, there is no head verb
    if head == 0: return None

    # base case returns the first head verb encountered
    if "VB" in dependencies[head].typ: return dependencies[head]

    # if this isn't a position where we can get an answer, recurse to the head node
    return getHeadVerb(dependencies, head)

# returns the number of words and punctuation in the given tree
def getNumIds(tree:st.models.constituency.parse_tree.Tree):
    num = 0
    children = tree.children
    for branch in children:
        if branch.label == str(branch):
            num += 1
        else:
            num += getNumIds(branch)

    return num

# given a tree structure and a target string, get the NP that the string is a noun in
def getNPfromNNx(   tree:st.models.constituency.parse_tree.Tree, 
                    text:str, 
                    noun_found:bool = False, 
                    NP_found:bool = False
                    ):
    label = tree.label
    children = tree.children

    if len(children) == 0:
        return (tree, False, False)

    res_tree = None

    # basically, we want to find the noun first, then return some value saying we found that and are now looking for the
    # smallest NP phrase it is in.
    # then, set a flag to ignore all other NPs when returning that simplest NP phrase
    for branch in children:
        # recurse first
        (temp_tree, noun_found, NP_found) = getNPfromNNx(branch, text, noun_found, NP_found)
        # check if this is the noun
        if not noun_found:
            if branch.label == str(branch) and "NN" in label and branch.label.lower().lstrip().rstrip() == text.lower().lstrip().rstrip():
                return (res_tree, True, NP_found)
        # if the noun has been found, check if this is the NP phrase
        elif not NP_found:
            if branch.label == "NP":
                return (branch, noun_found, True)
        # if both the noun and NP have been found, just make sure res_tree is updated for the return value
        else:
            res_tree = temp_tree
    
    return (res_tree, noun_found, NP_found)
        

def getPhrases(pipe2, tree:st.models.constituency.parse_tree.Tree, og_text:str, dependencies:dict):
    verb_phrases = {}
    prep_phrases = {}
    noun_lists = {}
    nouns = []
    return getPhrasesRecurs(pipe2, tree, verb_phrases, prep_phrases, noun_lists, og_text, tree, dependencies, 0, nouns)

def getPhrasesRecurs(   pipe2,
                        tree:st.models.constituency.parse_tree.Tree, # the stanza-generated constituency tree currently being analyzed (recursively)
                        verb_phrases:dict, # a dictionary of verb phrases: the verb and the phrase it represents
                        prep_phrases:dict, # a dictionary of preposition phrases, will be useful for questions
                        noun_lists:dict, # a dictionary of lists of nouns with the type (AND, OR, UNSPECIFIED) of list, list member nouns, and the verb of the encapsulating verb phrase
                        og_text:str, # the original sentence string
                        og_tree:st.models.constituency.parse_tree.Tree, # the whole tree for the step
                        dependencies:dict, # a dictionary of dependency relations, going from a word id to data where one can find its head or to the words dependent on it
                        num_words_before: int, # the number of words before the current phrase being analyzed. Useful for referencing the dependencies dict
                        nouns_cat: list # a simple list of nouns and compound nouns
                        ):
    # do a search through the consistuency tree to retrieve the prepositional phrase
    # also identify whether it is referring to a location on a food item or an appliance (cookware)

    label = tree.label
    children = tree.children

    num_ids_in_phrase = 0

    # do analysis of thing
    # look for NP, VP, PP

    # look for NP lists and combo nouns

    # first, it must be a Noun phrase for it to contain a list of nouns or a combo noun.
    if label == "NP":
        # first, let's check if this is a compound noun and if so, add it to our list of nouns, ex: lemon zest
        isCN = isComboNounPhrase(tree)
        if isCN and all(not constituency_to_str(tree) in nn[0] for nn in nouns_cat):
            # print("*" + constituency_to_str(tree) + "*")
            head_verb = getHeadVerb(dependencies, num_words_before + num_ids_in_phrase + getNumIds(tree))
            if head_verb != None: head_verb = head_verb.text
            nouns_cat.append((constituency_to_str(tree), head_verb))
            # print(constituency_to_str(tree))

        # now check if it is a list so check for ",", ";", or "and" or "or"
        isList = False
        list_type = None
        for child in children:
            if child.label == ";" or child.label == "," or (child.label == "CC" and (child.children[0].label.lower() == "and" or child.children[0].label.lower() == "or")):
                isList = True
                if child.children[0].label.lower() == "and":
                    list_type = ListType.AND
                elif child.children[0].label.lower() == "or":
                    list_type = ListType.OR

        if list_type == None:
            list_type = ListType.UNSPECIFIED

        # note that there might be sublists like "flour, sugar, and 'apples or oranges'", so just check for "or" and "and" within the NP children directly to determine list type
        if isList:

            # get the list of nouns in the NP
            nouns = []
            temp_noun_list = getAllOfTypes(children, ["NN", "NNS", "NNP", "NNPS"])
            # print(temp_noun_list)
            for ii in temp_noun_list:
                nouns.append(ii)
            

            # get the grouping verb based on dependency
            # print(num_words_before + num_ids_in_phrase + getWordsRecurs(children, []).index(getFirstTypeBroad(children, "NN").children[0].label)+1)
            firstNounWordinList = getFirstTypeBroad(children, "NN").children[0].label
            gr_verb = getHeadVerb(dependencies, num_words_before + num_ids_in_phrase + getWordsRecurs(children, []).index(firstNounWordinList)+1)
            if gr_verb != None:
                for dp in gr_verb.deps.keys():
                    if any(xx in gr_verb.text.lower() for xx in separation_labels):
                        break
                    if gr_verb.deps[dp][2] in ["obl", "obj"] and all(not gr_verb.deps[dp][1] in xx for xx in nouns):
                        # print(str(gr_verb.deps[dp][1]))
                        NP_res = getNPfromNNx(og_tree, gr_verb.deps[dp][1], False, False)
                        if NP_res[0] == None: continue
                        temp_obj = constituency_to_str(NP_res[0])
                        if all(not temp_obj in yy for yy in nouns) and isIngredient(pipe2, temp_obj, {}):
                            nouns.append(temp_obj)
                        # print(constituency_to_str(getNPfromNNx(og_tree, gr_verb.deps[dp][1], False, False)[0]))

                # print("LIST:")
                # print(gr_verb)
                # print(nouns)
                if gr_verb != None: gr_verb = gr_verb.text
            noun_lists[len(noun_lists.keys())] = ((list_type, nouns, gr_verb))
        
    # add any straggler nouns to the noun list
    if label in ["NN", "NNS", "NNP", "NNPS"]:
        noun = children[0].label
        if all(not noun.lower() in noun_coll[0].lower() for noun_coll in nouns_cat):
            head_verb = getHeadVerb(dependencies, num_words_before + num_ids_in_phrase + 1)
            if head_verb != None: head_verb = head_verb.text
            nouns_cat.append((noun, head_verb, num_words_before + num_ids_in_phrase + 1))

    # look for VP phrase without sub VP branches
    # later remove the one corresponding to the root verb, so we just have the extraneous instructions
    if label == "VP":
        if all((x.label != "VP") for x in children):
            temp_res = getFirstType(children, "VB")

            if temp_res != None and temp_res.children[0].label.lower() != "let":
                verb_phrases[len(verb_phrases.keys())] = (temp_res.children[0].label, constituency_to_str(tree))
            
    # look for prepositions for certain details (IE "in the oven")
    if label == "PP" or label == "SBAR":
        temp_res = getFirstType(children, "IN")
        if temp_res != None and all(not constituency_to_str(tree) in prep_phrases[pp][1] for pp in prep_phrases):
            head_verb = getHeadVerb(dependencies, num_words_before + num_ids_in_phrase + 1)
            if head_verb != None: head_verb = head_verb.text
            prep_phrases[len(prep_phrases.keys())] = (temp_res.children[0].label, constituency_to_str(tree), head_verb)
    if label == "PRT":
        temp_res = getFirstType(children, "RP")
        if temp_res != None:
            # if we just add like above, we will only get the RP word but we want the object of the VP this PRT is in, so let's get that object
            # first, get the head of this RP
            # print(num_words_before + num_ids_in_phrase + 1)
            RP_text = constituency_to_str(tree)
            head_wrd = dependencies[dependencies[num_words_before + num_ids_in_phrase + 1].head_id]
            for dep_id in head_wrd.deps:
                # print(head_wrd.deps[dep_id][0])
                if head_wrd.deps[dep_id][2] == "obj":
                    RP_text += " " + getDepPhrase(dependencies, head_wrd.deps[dep_id][0])
            if(all(not RP_text in prep_phrases[pp][1] for pp in prep_phrases)):
                head_verb = getHeadVerb(dependencies, num_words_before + num_ids_in_phrase + 1)
                if head_verb != None: head_verb = head_verb.text
                prep_phrases[len(prep_phrases.keys())] = (temp_res.children[0].label, RP_text, head_verb)
    if "ADV" in label:
        temp_res = getFirstType(children, "RB")
        if temp_res != None:
            head_verb = getHeadVerb(dependencies, num_words_before + num_ids_in_phrase + 1)
            if head_verb != None: head_verb = head_verb.text
            prep_phrases[len(prep_phrases.keys())] = (temp_res.children[0].label, constituency_to_str(tree), head_verb)


    # recurse to children
    
    # print(childr)
    if len(children) == 0 or str(tree) == label: # base case
        return (verb_phrases, prep_phrases, noun_lists, num_ids_in_phrase, nouns_cat)
    else: # go over all child branches
        for branch in children:
            if str(branch) == branch.label:
                num_ids_in_phrase += 1
            if str(branch) != "," and str(branch) != branch.label:
                # print(branch)
                (verb_phrases, prep_phrases, noun_lists, temp_num, nouns) = getPhrasesRecurs(pipe2, branch, verb_phrases, prep_phrases, noun_lists, og_text, og_tree, dependencies, num_words_before + num_ids_in_phrase, nouns_cat)
                num_ids_in_phrase += temp_num

    return (verb_phrases, prep_phrases, noun_lists, num_ids_in_phrase, nouns_cat)

    






def doParsing(pipe2, depgram, test_phrase:str, ingredient_list:list):

    
    test_doc = depgram(test_phrase)

    # print(test_doc.depparse)

    # print(test_doc)
    # print(test_doc.entities)
    steps = {}
    curr_id = 1
    noun_seen = {}
    adj_seen = {}

    # dict of ingredient combinations with integer ids as keys and values:
    #   the list of constituent nouns as tuples with if they are 
    hierarchy = {}

    for sent in test_doc.sentences:
        consti = sent.constituency
        (dep, name_to_dep_ids) = getDependency(sent.dependencies)
        # for ti in dep.keys():
            # print(dep[ti])
            # print(ti)
        # print(consti)
        # print(consti.label) 
        # print(consti.children) # do some tree traversal to find preposition phrases and add them to details(?) Probably BFS
        # sent.print_dependencies()
        # print(consti.children[0]) # the useful data
        # print(type(consti))
        # print(sent.text)

        # print(constituency_to_str(consti))
        (verb_phrases, prep_phrases, noun_lists, _, nouns_phr) = getPhrases(pipe2, consti.children[0], sent.text, dep)
        # print("verb phrases: " + str(verb_phrases))
        # print("prep phrases: " + str(prep_phrases))
        # print("noun lists: " + str(noun_lists))
        # print("nouns: " + str(nouns_phr))
        # getPhrases(consti.children[0], sent.text)

        root = ""
        actions = {}
        ingredients = {}
        tools = {}
        details = {}

        nouns_seen = {}

        for wrd in sent.words:

            if wrd.deprel == "punct":
                continue
            
            # print(wrd.text, wrd.lemma)
            # print("\t" + wrd.pos)
            # print("\thead: " + str(wrd.head-1) + " " + head_word.text) # note ID is 1-indexed, NOT 0-indexed
            # print("\t" + wrd.deprel)
            # if wrd.feats != None: 
            #     print("\t" + wrd.feats)

            if wrd.deprel == "root":
                root = wrd.text
                continue


        # print("STARTING ZERO SHOT")
        for nn in nouns_phr:
            (res, nouns_seen) = getNounType(pipe2, nn[0], nouns_seen)
            (ingr, nouns_seen) = isIngredient(pipe2, nn[0], nouns_seen)
            (tool, nouns_seen) = isTool(pipe2, nn[0], nouns_seen)
            if ingr:
                ingredients[nn[0]] = (nn[0], nn[1], res) # change later to be something like all the ingredients that make it up
            elif tool:
                # print(tools)
                tools[nn[0]] = (nn[0], nn[1], res) 
        # print("END OF ZERO SHOT")
        # print(nouns_seen)

        details = prep_phrases
        
        # create hierarchies for noun_lists
        for nn in noun_lists.keys():
            noun_lists[nn]

        steps[curr_id] = Step(curr_id, root, verb_phrases, ingredients, tools, details, sent.text)
        
        curr_id += 1
    

    return steps
# (ROOT (S (VP (VB Divide) (NP (DT the) (NN batter)) (PP (IN between) (NP (DT the) (VBN prepared) (NNS pans)))) (. .)))

