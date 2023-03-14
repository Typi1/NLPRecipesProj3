import stanza as st
import re as re

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

# returns a list with each entry corresponding to a dependent word on the head word provided
# (word text, relation to head, word type, id in dependency dict)
# ex: ("it", "obj", "PRP", 5)
def getDepInfo(input_deps:dict, head:depNode):
    res = []
    for dd in head.deps:
        text = head.deps[dd][1]
        rel_type = head.deps[dd][2]
        word_type = input_deps[head.deps[dd][0]].typ
        res.append((text, rel_type, word_type, head.deps[dd][0]))
    return res





class Ingredient:
    def __init__(   self, 
                    og_text:str, # the original string
                    main_comp:str, # the main part of the ingredient component, IE chicken
                    quantity:str, # a number. if a non-numerical amount, this should be None (ex: some raisins). "a" -> 1. is a string rather than a float bc fractions are more readable for recipes
                    measurement:str, # the measurement the quantity is referring to (like a cup). if no measurement (like "2 apples"), is None. if vague, non-committal amount (ex: "some"), this does here.
                    sub_quantity:str, 
                    sub_measurement: str,
                    descriptors:list # other details of the ingredient listing, IE dependent nouns, adjectives, preparation verb parts (ex: "finely chopped")
                    ):
        self.og_text = og_text
        self.main_comp = main_comp
        self.quantity = quantity
        self.measurement = measurement
        self.sub_quantity = sub_quantity
        self.sub_measurement = sub_measurement
        self.descriptors = descriptors

    def __str__(self):
        outputStr = ""
        outputStr += "Ingredient: " + self.main_comp
        outputStr += "\n\tQuantity: " 
        if self.quantity == None:
            outputStr += "N/A"
        else:
            outputStr += self.quantity
        outputStr += "\n\tMeasurement: " 
        if self.measurement == None:
            if self.sub_quantity == None and self.sub_measurement == None:
                outputStr += "N/A"
            else:
                outputStr += self.sub_quantity + " " + self.sub_measurement + " "
        else:

            if self.sub_quantity != None:
                outputStr += self.sub_quantity + " " 
            if self.sub_measurement != None:
                outputStr += self.sub_measurement + " "

            outputStr += self.measurement
        
        outputStr += "\n\tDescriptors: "
        if len(self.descriptors) < 1:
            outputStr += "\n\t\tN/A"
        else:
            for dt in self.descriptors:
                outputStr += "\n\t\t" + dt
        outputStr += "\n\tOriginal text: " + self.og_text
        return outputStr

def combineItemsIntoPhrase(its:list):
    res = ""
    for x in its:
        if x in [".", ",", "'", ";", ":", "-", "/"] or (len(x) > 1 and x[0] in [".", ",", "'", ";", ":", "-", "/"]):
            res = res.rstrip()
            
        res += x
        res += " "  
    res = res.replace("&#39;", "'")
    return res.rstrip()

def floatFromFractionString(frac: str):
    try:
        return float(frac)
    except:
        numerator = frac[:frac.index("/")]
        denominator = frac[frac.index("/")+1:]

        return float(numerator) / float(denominator)

# tries to find a quantity and measurement if none were found by directly analyzing the head word
def tryFindQuantity(input_deps:dict, head:depNode, head_rel_type:str, meas: str):
    quantity = None
    measurement = None

    # if measurement, then set measurement
    if head_rel_type == "nmod:npmod":
        measurement = head.text

    if head_rel_type in ["nummod", 'det']:
        if head_rel_type == 'det' and head.text.lower() in ["a", "an"]:
            # print("???")
            return (str(1), measurement)
        elif head_rel_type == 'det' and meas != None:
            # print("???")
            return (head.text, measurement)
        elif head_rel_type == "nummod":
            # print("???")
            return (head.text, measurement)

    for dd in head.deps:
        rel_type = head.deps[dd][2]
        # print(head.deps[dd])
        (temp_quantity, temp_measurement) = tryFindQuantity(input_deps, input_deps[head.deps[dd][0]], rel_type, measurement)
        if temp_measurement != None:
            measurement = temp_measurement
        if temp_quantity != None:
            # print(temp_quantity)
            if quantity == None:
                quantity = temp_quantity
            else:
                quantity == str(floatFromFractionString(quantity) * floatFromFractionString(temp_quantity))
            if measurement == None:
                measurement = head.text


    return (quantity, measurement)

# returns an ingredient data structure based on the ingredient string provided
def getIngredientParameters(depgram, ingred:str):
    og_ingred = ingred
    sub_phrase = None
    sub_quantity = None
    sub_measurement = None
    after_comma = None
    if "(" in ingred and ")" in ingred:
        sub_measurement_result = re.search("\((.+)\)", ingred)
        if sub_measurement_result != None:
            sub_phrase = sub_measurement_result.group(1)
            # print(sub_phrase)
            ingred = ingred.replace(sub_phrase, "")
            nums = re.search("\s*([\d/\.]+)\s*", sub_phrase)
            if nums != None:
                sub_quantity = nums.group(1)
                sub_measurement = sub_phrase[nums.span()[1]:]

        ingred = ingred.replace("(", "")
        ingred = ingred.replace(")", "")

    if "," in ingred:
        comma_result = re.search("\,(.+)", ingred)
        if comma_result != None:
            after_comma = comma_result.group(1)
            ingred = ingred.replace(after_comma, "")
            ingred = ingred.replace(",", "")



    doc = depgram(ingred)

    # consti = doc.sentences[0].constituency
    depend = getDependency(doc.sentences[0].dependencies)[0]
    head_dep = depend[list(depend[0].deps.keys())[0]]
    # print(head_dep)
    # print(consti)

    # for dd in depend:
    #     print(depend[dd])

    # from what I can tell, the head noun will reference 4 common types of dependent relations:
    #   1: "amod" | "parataxis": should go into the descriptors list [note that the parataxis is something weird where if there is a comma or something]
    #   2: "compound": should be part of the main_comp (make sure to figure out how to enjoin with the head word)
    #   3: "nmod:npmod": should be the measurement field. if it exists, we need to go there and get the nummod or a de ("a", "some", etc.)
    #   4: "nummod": this should be the quantity field. if this is dependent on the root noun, then there is no measurement word, so set it to None
    
    descriptors = []
    compounds = []
    measurement = None
    quantity = None
    main_comp = head_dep.text
    
    deps = getDepInfo(depend, head_dep)
    # print(deps)
    
    for dd in deps:
        if dd[1] == 'nmod:npmod':
            measurement = dd[0]
            temp_quant = getDepInfo(depend, depend[dd[3]])
            if temp_quant == None:
                continue
            for tq in temp_quant:
                if tq[0] == 'no':
                    continue
                if tq[1] == 'nummod':
                    quantity = tq[0]
                elif tq[1] == 'det' and (tq[0].lower() == 'a' or tq[0].lower() == 'an'):
                    quantity = str(1)
                elif quantity == None:
                    quantity = tq[0]
                    # note no break here bc this is a failsafe in case there is no appropriate quantity descriptor
        elif dd[1] == 'amod' or dd[1] == 'parataxis' or dd[1] == 'conj' or dd[1] == 'acl':
            # also add certain dependents on the amod if they exist (ex: "all-purpose flour" has "all" as dependent on "purpose")
            temp_text = dd[0]
            temp_desc = getDepInfo(depend, depend[dd[3]])
            temp_adds = []
            if temp_desc != None:
                for td in temp_desc:
                    if td[1] in ['det', 'amod', 'obl']:
                        temp_adds.append(td[0])
                    elif td[1] in ['punct']:
                        continue
                    else:
                        # print("What is this?? " + str(td))
                        continue
            if len(temp_adds) > 0:
                temp_adds = [temp_text] + temp_adds
                temp_text = combineItemsIntoPhrase(temp_adds)
            descriptors.append(temp_text)
        elif dd[1] == 'compound' or dd[1] == 'appos' or dd[1] == 'aux':
            remove_list = ["package", "packages", "can", "cans", "jar", "jars", "container", "containers"]
            if dd[0] in remove_list:
                measurement = dd[0]
            else:
                # print(">>>" + str(depend[dd[3]]))
                for abc in list(depend[dd[3]].deps.keys()):
                    # print(depend[dd[3]].deps[abc])
                    # print(depend[abc])
                    if depend[dd[3]].deps[abc][2] == 'amod':
                        compounds.append(depend[abc].text)
                # print(list(depend[dd[3]].deps.keys()))
                compounds.append(dd[0])
        elif dd[1] == 'nummod':
            quantity = dd[0]
        elif dd[1] == 'det':
            if dd[0].lower() == 'a' or dd[0].lower() == 'an':
                quantity = str(1)
            else:
                if dd[0].lower() == 'no':
                    compounds.append(dd[0])
                    continue
                quantity = dd[0]
        elif dd[1] in ['aux', 'punct']:
            continue
        else:
            # print("??????")
            # descriptors.append(dd[0])
            # print(dd)
            continue

    if quantity == None and measurement == None:
        # do something to try and find something because we should have at least 1

        # first, let's try going through each of the compounds recursively with depth-first
        # temp_quant = None
        # temp_meas = None
        for cc in deps:
            (temp_quant, temp_meas) = tryFindQuantity(depend, depend[cc[3]], None, None)
            if quantity == None and temp_quant != None:
                quantity = temp_quant
                
            if measurement == None and temp_meas != None:
                measurement = temp_meas
                
            if quantity != None and measurement != None:
                break


    if len(compounds) > 0:
        compounds.append(main_comp)
        main_comp = combineItemsIntoPhrase(compounds)

    if after_comma != None:
        descriptors.append(after_comma.lstrip().rstrip())

    return Ingredient(og_ingred, main_comp, quantity, measurement, sub_quantity, sub_measurement, descriptors)

# wrapper function for getIngredientParameters.
# input:
#   depgram, aka the stanza pipeline thing 
#   a list of strings where each string is an ingredient description
# output: a list of corresponding ingredient data structures (see above Ingredient class)
def parseIngredients(depgram, ingredients:list):
    ingredients_data = []
    for ii in ingredients:
        ingredients_data.append(getIngredientParameters(depgram, ii))

    return ingredients_data