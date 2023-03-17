import stanza as st
import re
import ingredients_parser
import steps_parser_ver2 as spv2
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import requests



def get_soup(url:str):
    response = requests.get(url)
    return BeautifulSoup(response.text, "html.parser")

chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def get_substitute_list(query:str):
    query = re.sub("[.,;!]", "", query)
    if query == "": return None
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    url = "https://foodsubs.com/groups?a=&name=" + query
    driver.get(url)
    query_html = BeautifulSoup(driver.page_source, 'html.parser')
    # print(query_html.prettify())
    # print(query_html.find('a', class_ ="card-learn-more").attrs['href'])
    url_seg = query_html.find('a', class_ ="card-learn-more")
    if url_seg == None:
        # print("NO SUBSTITUTES FOUND")
        new_query = re.search("(\S+)",query)
        if new_query == None: return None
        new_query = query[new_query.span()[1]:]
        return get_substitute_list(new_query.lstrip())
    
    new_url = "https://foodsubs.com" + url_seg.attrs['href']
    # print(new_url)
    driver.get(new_url)
    page_html = BeautifulSoup(driver.page_source, 'html.parser')
    results_seg = page_html.find(lambda x: x.name == "div" and x.get('class') == ["ingredients-table"])

    if results_seg == None:
        new_query = re.search("(\S+)",query)
        if new_query == None: return None
        new_query = query[new_query.span()[1]:]
        return get_substitute_list(new_query.lstrip())

    results_seg = results_seg.findAll(lambda y: y.name == "div" and y.get('class') == ["row"])

    if results_seg == None:
        new_query = re.search("(\S+)",query)
        if new_query == None: return None
        new_query = query[new_query.span()[1]:]
        return get_substitute_list(new_query.lstrip())
    
    # print(results_seg)

    relevant = []

    for ii in results_seg:
        # print(ii.text)
        if re.search("\d+\s+Cals.", ii.text) != None:
            candidate_dict = {}
            # print(ii)
            cd = ii.find("div", class_="col-md-3 sub-details sub-details-last")
            if cd == None:
                continue
            candidate_dict["name"] = cd.find('a').text
            candidate_dict["warning"] = ii.find("div", class_="sortable-column col-md-2").text
            measurements = ii.findAll(lambda x: x.name == "div" and (x.get('class') == ['sortable-column', 'col-md-1'] or x.get('class') == ["col-md-fixed"]))
            counter = 0
            for mm in measurements:
                if counter == 1:
                    candidate_dict["calories"] = (mm.text, float(re.search("([\d\.]+)", mm.text).group(1)))
                elif counter == 2:
                    candidate_dict["salt"] = (mm.text, float(re.search("([\d\.]+)", mm.text).group(1)))
                elif counter == 3:
                    candidate_dict["fat"] = (mm.text, float(re.search("([\d\.]+)", mm.text).group(1)))
                elif counter == 4:
                    candidate_dict["cholesterol"] = (mm.text, float(re.search("([\d\.]+)", mm.text).group(1)))
                elif counter == 8:
                    candidate_dict["sugar"] = (mm.text, float(re.search("([\d\.]+)", mm.text).group(1)))
                counter += 1
            # print(candidate_dict)
            if counter == 13:
                relevant.append(candidate_dict)

    return relevant

# ranks from healthiest to least healthy
# input is a list from the output of get_substitute_list
def rankHealthy(subst:list):
    temp_list = []
    for sl in subst:
        if sl['calories'][1] == 0: continue
        unhealth_score = 0
        unhealth_score += sl['cholesterol'][1] * 2
        unhealth_score += sl['fat'][1]
        unhealth_score += sl['salt'][1]
        unhealth_score += sl['sugar'][1]
        unhealth_score /= sl['calories'][1]
        temp_list.append((sl['name'], unhealth_score))
    temp_list.sort(key=lambda x: x[1])

    # print(temp_list)

    res_list = []
    for tl in temp_list:
        res_list.append(tl[0])

    return res_list

# filters out ingredients with meat in them
def getNonMeat(subst:list):
    meat_labels = ['meat', 'pork', 'chicken', 'fish', 'beef', 'lamb']
    nm_list = []
    for sl in subst:
        if not any(ml in sl['warning'] for ml in meat_labels):
            nm_list.append(sl)
    # print(nm_list)
    return nm_list

# filters out ingredients without meat in them
def getMeat(subst:list):
    meat_labels = ['meat', 'pork', 'chicken', 'fish', 'beef', 'lamb']
    nm_list = []
    for sl in subst:
        if any(ml in sl['warning'] for ml in meat_labels):
            nm_list.append(sl)
    # print(nm_list)
    return nm_list

# filters out ingredients with gluten in them
def getGlutenFree(subst:list):
    ng_list = []
    for sl in subst:
        if not 'gluten' in sl['warning']:
            ng_list.append(sl)

    return ng_list

# filters out ingredients with dairy in them
def getDairyFree(subst:list):
    nd_list = []
    for sl in subst:
        if not 'dairy' in sl['warning']:
            nd_list.append(sl)

    return nd_list

def get_substitute(query:str):
    query = re.sub("[.,;!]", "", query)
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    url = "http://www.google.com/search?q=" + query + "&start=" + str((0))
    driver.get(url)
    query_html = BeautifulSoup(driver.page_source, 'html.parser')
    results = query_html.find('div', id="search")
    results = results.find('div', class_="v7W49e")
    results = results.find('div', class_="MjjYud")
    first_attempt = results.find_all('li', class_="TrT0Xe")
    substitutes = []
    if not first_attempt:
        second_attempt = results.find('span', class_="ILfuVd")
        if not second_attempt:
            third_attempt = results.find_all('span', {"class": None, "id": None, "data-ved": None})
            substitutes.append(third_attempt[-1].text)
        else:
            substitutes.append(second_attempt.text)
    else:
        for result in first_attempt:
            result = result.text.split('.')[0]
            substitutes.append(result)
    
    if substitutes:
        # print("No worries. Here are the substitutes. \n")
        # counter = 1
        # for s in substitutes:
            # print(f"{counter}. {s}")
            # counter += 1
            # print()
        return substitutes
    else:
        # print('error??')
        pass

def floatFromFractionString(frac: str):
    try:
        return float(frac)
    except:
        numerator = frac[:frac.index("/")]
        denominator = frac[frac.index("/")+1:]

        return float(numerator) / float(denominator)

# checks the zero-shot rating between a potential member and a categorical grouping (ex: "grape", "fruit" should yield a high value)
def checkMembership(pipe2, test:str, category:str):
    return pipe2(test, category)['scores'][0]

# returns a list of webscraped substitutions for input ingredient, with the parameter keywords added
def getSubList(target:str, parameters:list):
    res_string = "what can I substitute for " + target
    for pp in parameters:
        res_string += pp + " "
    return get_substitute(res_string)

# returns a logical string for the quantity of the ingredient one needs
def getQuantityString(ingr:ingredients_parser.Ingredient, multiplier: float):
    res = ""
    if ingr.quantity != None:
        if multiplier != 1:
            res += str(floatFromFractionString(ingr.quantity) * multiplier)
        else:
            res += ingr.quantity
    if (ingr.sub_quantity != None or ingr.sub_measurement != None) and ingr.quantity != None:
        res += " ("
    if ingr.sub_quantity != None:
        if ingr.quantity == None and multiplier != 1:
            res += str(floatFromFractionString(ingr.sub_quantity) * multiplier) + " "
        else:
            res += ingr.sub_quantity + " "
    if ingr.sub_measurement != None:
        res += ingr.sub_measurement
    if (ingr.sub_quantity != None or ingr.sub_measurement != None) and ingr.quantity != None:
        res = res.rstrip()
        res += ")"
    if ingr.measurement != None:
        res += " " + ingr.measurement

    return res.lstrip().rstrip()





action_priority_list = ['bake', 'boil', 'fry', 'cook', 'flambe', 'microwave', 'steam', 'broil', 'grill', 'roast', 'sear', 'saute', 'sauté','poach', 'simmer', 'braise', 'barbeque', 'barbecue',# cooking methods have priority
                        'freeze','cool','refrigerate' # then freezing/cooling methods
                        ]

# given the steps data and depgram, return (list of all tools, list of all actions, the main action)
def get_Tools_Actions_List(depgram, steps):
    all_tools = []
    all_actions = []
    for j in steps:
        # print(steps[j])
        for aa in steps[j].actions:
            all_actions.append(steps[j].actions[aa][1].lower())
        for tt in steps[j].tools:
            curr_tool = steps[j].tools[tt][2]
            
            if curr_tool != '':
                all_tools.append(curr_tool)
                

    all_tools.sort(key=lambda x: len(x), reverse=True)

    
    selected_tools = []
    for tt in all_tools:
        t_consti = depgram(tt).sentences[0].constituency
        
        if "(VP" in str(t_consti) or "(RB" in str(t_consti):
            continue
        elif (any(spv2.isDerivativeOfSecond(tt, xx)[1] > 0 for xx in selected_tools) and len(re.findall(tt, str(all_tools))) < 4) or tt in selected_tools:
            # print(re.findall(tt, str(all_tools)))
            continue
        else:
            selected_tools.append(tt)

    # TOOL LIST
    # print(selected_tools)

    main_action = ""
    for ap in action_priority_list:
        if any(spv2.isDerivativeOfSecond(ap,aa)[1] > 0 for aa in all_actions):
            main_action = ap
            break

    if main_action == "":
        main_action = all_actions[0]

    # PRIMARY COOKING METHOD
    # print(main_action)

    return (selected_tools, all_actions, main_action)






### MAKE HEALTHY
def makeHealthy(pipe2, ingredients: list, main_action: str, action_priority_list: list):
    new_instructions = []

    min_transforms = 4

    # ingredient word as key to an array of options. this array is made of tuples for suggestions. the 1st (not 0th) element specifies whether it is a quantity mod ('multi'), a substitution ('sub'), or a modded ver ('mod')
    healthy_ingr_subs = {'chocolate':[('dark', 'mod'), ('hazelnut', 'sub')], 'sugar':[('coconut sugar', 'sub'), (0.75, 'multi')], 'salt':[(0.25, 'multi')], 'cheese':[('reduced-fat', 'mod')], 'milk':[('skim', 'mod'), ('almond milk', 'sub')]}

    # basically, just analyze the steps, ingredients, and main cooking action to see what can be made healthier through IF statements, and maybe webscraped substitutions

    # first, if the cooking method is unhealthy, change it
    if main_action == "fry":
        new_instructions.append("Instead of frying, try sauteing instead. This means to not use very much cooking oil in the pan, though a little bit to keep it from sticking is recommended. It should take around the same amount of time as frying.")

    # now, go through the ingredients
    num_subs = 0 # counter for the number of substitutions made. if not at least 3 substitions are made, do some later

    ingr_seen = []
    subst_seen = []

    for ingr in ingredients:

        # replace meats with healthier meats
        isMeat = checkMembership(pipe2, ingr.main_comp, 'meat')
        isFish = checkMembership(pipe2, ingr.main_comp, 'fish')
        isFruit = checkMembership(pipe2, ingr.main_comp, 'fruit')
        # 'turkey' in ingr.main_comp
        # 'chicken' in ingr.main_comp
        # print(ingr.main_comp + ": " + str(isMeat))
        # print(ingr.main_comp + ": " + str(isFish))
        if (isMeat > 0.8 and isFish < 0.2 and not 'turkey' in ingr.main_comp.lower() and not 'chicken' in ingr.main_comp.lower()) and isFruit < 0.5  and not "water" in ingr.main_comp.lower():
            if "sauce" in ingr.main_comp.lower() or "broth" in ingr.main_comp.lower(): continue
            new_instructions.append("Instead of " + ingr.main_comp + ", it would be healthier to use chicken or turkey (we will default to chicken). You can use the same amount (" + getQuantityString(ingr, 1) + "), though it may take longer to cook than red meats since you don't want it \"rare.\"")
            num_subs += 1
            # ingr.main_comp = "chicken"
            continue
        # print(getQuantityString(ingr, 0.5))
        
        # go through healthy ingr subs and do those substitutions
        for hk in healthy_ingr_subs.keys():
            if spv2.isDerivativeOfSecond(hk, ingr.main_comp)[1] > 0:
                # different things to say based on if there are mod, sub, or multi tagged suggestions
                # first, sort the diff tag suggestions into different lists
                ingr_seen.append(ingr.main_comp)
                tags = healthy_ingr_subs[hk]
                modss = []
                subss = []
                multis = []
                for tt in tags:
                    if tt[1] == "mod":
                        modss.append(tt[0])
                    elif tt[1] == "sub":
                        subss.append(tt[0])
                    elif tt[1] == "multi":
                        multis.append(tt[0])

                ingr_res = ""
                for mm in modss:
                    ingr_res += "You can use a " + mm + " version of " + ingr.main_comp + " instead to make this healthier. "
                for su in subss:
                    if su in subst_seen:
                        sub_list = get_substitute_list(ingr.main_comp)
                        if sub_list == None: continue
                        sub_list = rankHealthy(sub_list)
                        if len(sub_list) < 1: continue
                        counter = 0
                        while counter < len(sub_list) and sub_list[counter].lower() in subst_seen:
                            counter += 1
                        if counter >= len(sub_list): continue
                        ingr_res += "You could substitute " + ingr.main_comp + " with " + sub_list[counter].lower() + ". "
                        subst_seen.append(sub_list[counter].lower())
                        continue
                    ingr_res += "You could substitute " + ingr.main_comp + " with " + su + ". "
                    subst_seen.append(su)
                for mu in multis:
                    if getQuantityString(ingr,1) == "": continue
                    ingr_res += "If you don't want to replace " + ingr.main_comp + ", you could use " + str(mu) + " of the original amount: "  + getQuantityString(ingr,1) + " (new amount: " + getQuantityString(ingr, mu) + "). "

                new_instructions.append(ingr_res)
                num_subs += 1
                break

    if num_subs < min_transforms:
        for ingr in ingredients:
            # skip past ingredients we already have a transformation for
            if ingr.main_comp in ingr_seen:
                continue
            # find a substitution for an untransformed ingredient
            # new_sub = getSubList(ingr.main_comp, ["healthy"])[0]
            sub_list = get_substitute_list(ingr.main_comp)
            if sub_list == None: continue
            sub_list = rankHealthy(sub_list)
            if len(sub_list) < 1: continue
            new_instructions.append("You could substitute " + ingr.main_comp + " with " + sub_list[0].lower() + ".")
            num_subs += 1
            if num_subs >= min_transforms:
                break 

    # for abc in new_instructions:
    #     print(abc)
    return new_instructions

### MAKE UNHEALTHY

# replace oils with melted butter
# add more salt or just some salt in general lol
# extra sugar if there is sugar
# add whipped cream or heavy cream if sugar
# pan cooking methods -> fry
# white meat/fish -> red meat

def makeUnhealthy(pipe2, ingredients: list, main_action: str, action_priority_list: list):
    new_instructions = []

    min_transforms = 4

    # ingredient word as key to an array of options. this array is made of tuples for suggestions. the 1st (not 0th) element specifies whether it is a quantity mod ('multi'), a substitution ('sub'), or a modded ver ('mod')
    unhealthy_ingr_subs = {'oil':[('corn', 'mod'), ('melted butter', 'sub')], 'sugar':[(1.25, 'multi'), ('saccharin', 'sub')], 'salt':[(1.25, 'multi')], 'egg':[('1.5', 'multi')], 'milk':[('heavy cream', 'sub')]}

    # basically, just analyze the steps, ingredients, and main cooking action to see what can be made healthier through IF statements, and maybe webscraped substitutions

    # first, if the cooking method is healthy and not baking, change it to frying
    if any(spv2.isDerivativeOfSecond(apl, main_action)[1] > 0 for apl in ['flambe', 'steam', 'broil', 'grill', 'roast', 'sear', 'saute', 'sauté','poach', 'simmer', 'braise', 'barbeque', 'barbecue']):
        new_instructions.append("Instead of trying to " + main_action +  ", try frying instead. This means a pan, a stove, and a lot of oil are needed, though butter could also be used.")

    # now, go through the ingredients
    num_subs = 0 # counter for the number of substitutions made. if not at least 3 substitions are made, do some later

    ingr_seen = []
    subst_seen = []

    for ingr in ingredients:

        # replace meats with healthier meats
        isMeat = checkMembership(pipe2, ingr.main_comp, 'meat')
        isFish = checkMembership(pipe2, ingr.main_comp, 'fish')
        isWhiteMeat = checkMembership(pipe2, ingr.main_comp, 'white meat')
        isRedMeat = checkMembership(pipe2, ingr.main_comp, 'red meat')
        isFruit = checkMembership(pipe2, ingr.main_comp, 'fruit')
        # 'turkey' in ingr.main_comp
        # 'chicken' in ingr.main_comp
        # print(ingr.main_comp + ": " + str(isMeat))
        # print(ingr.main_comp + ": " + str(isFish))
        if (isFish > 0.8 or (isMeat > 0.8 and (isWhiteMeat > isRedMeat or "chicken" in ingr.main_comp.lower()))) and isFruit < 0.5  and not "water" in ingr.main_comp.lower():
            if "sauce" in ingr.main_comp.lower() or "broth" in ingr.main_comp.lower(): continue
            new_instructions.append("Instead of " + ingr.main_comp + ", it would be less healthy to use a red meat like beef, pork, lamb, etc. We'll default to beef. You can use the same amount (" + getQuantityString(ingr, 1) + "). Cooking time is up to you depending on how you want your meat done (well-done, medium, rare, etc.).")
            num_subs += 1
            # ingr.main_comp = "beef"
            continue
        # print(getQuantityString(ingr, 0.5))
        
        # go through unhealthy ingr subs and do those substitutions
        for hk in unhealthy_ingr_subs.keys():
            if spv2.isDerivativeOfSecond(hk, ingr.main_comp)[1] > 0:
                # different things to say based on if there are mod, sub, or multi tagged suggestions
                # first, sort the diff tag suggestions into different lists
                ingr_seen.append(ingr.main_comp)
                tags = unhealthy_ingr_subs[hk]
                modss = []
                subss = []
                multis = []
                for tt in tags:
                    if tt[1] == "mod":
                        modss.append(tt[0])
                    elif tt[1] == "sub":
                        subss.append(tt[0])
                    elif tt[1] == "multi":
                        multis.append(tt[0])

                ingr_res = ""
                for mm in modss:
                    ingr_res += "You can use a " + mm + " version of " + ingr.main_comp + " instead to make this unhealthier. "
                for su in subss:
                    if su in subst_seen:
                        sub_list = get_substitute_list(ingr.main_comp)
                        if sub_list == None: continue
                        sub_list = rankHealthy(sub_list)
                        if len(sub_list) < 1: continue
                        counter = 0
                        while counter < len(sub_list) and sub_list[counter].lower() in subst_seen:
                            counter += 1
                        if counter >= len(sub_list): continue
                        ingr_res += "You could substitute " + ingr.main_comp + " with " + sub_list[counter].lower() + ". "
                        subst_seen.append(sub_list[counter].lower())
                        continue
                    ingr_res += "You could substitute " + ingr.main_comp + " with " + su + ". "
                    subst_seen.append(su)
                for mu in multis:
                    if getQuantityString(ingr,1) == "": continue
                    ingr_res += "Use more " + ingr.main_comp + ". You could use " + str(mu) + " of the original amount: "  + getQuantityString(ingr,1) + " (new amount: " + getQuantityString(ingr, mu) + "). "

                new_instructions.append(ingr_res)
                num_subs += 1
                break

    if num_subs < min_transforms:
        if not 'salt' in ingr_seen:
            new_instructions.append("You could add 1/2 teaspoon of salt.")
            num_subs += 1
        for ingr in ingredients:
            # skip past ingredients we already have a transformation for
            if ingr.main_comp in ingr_seen:
                continue
            # find a substitution for an untransformed ingredient
            # new_sub = getSubList(ingr.main_comp, ["unhealthy"])[0]
            sub_list = get_substitute_list(ingr.main_comp)
            if sub_list == None: continue
            sub_list = rankHealthy(sub_list)
            if len(sub_list) < 1: continue
            new_instructions.append("You could substitute " + ingr.main_comp + " with " + sub_list[-1].lower() + ".")
            # new_instructions.append("You could substitute " + ingr.main_comp + " with " + new_sub.lower() + ".")
            num_subs += 1
            if num_subs >= min_transforms:
                break 

    # for abc in new_instructions:
    #     print(abc)
    return new_instructions


# makeUnhealthy(ingredients, main_action, action_priority_list)

### MAKE VEGETARIAN
# also try and do a bit of vegan-leaning stuff just to have more stuff changed

# replace meat/fish with tofu or eggplant (default to tofu)
# maybe have a message if the recipe doesn't seem to have meat in it
# replace eggs with some substitute
# replace milk with plant based milk
def makeVeg(pipe2, ingredients: list, main_action: str, action_priority_list: list):
    new_instructions = []

    min_transforms = 3

    # ingredient word as key to an array of options. this array is made of tuples for suggestions. the 1st (not 0th) element specifies whether it is a quantity mod ('multi'), a substitution ('sub'), or a modded ver ('mod')
    veg_ingr_subs = {'egg':[('aquafaba', 'sub')], 'cheese':[('cashew cheese', 'sub')], 'milk':[('almond milk', 'sub')], 'honey':[('maple syrup', 'sub')]}

    # basically, just analyze the steps, ingredients, and main cooking action to see what can be made healthier through IF statements, and maybe webscraped substitutions


    # now, go through the ingredients
    num_subs = 0 # counter for the number of substitutions made. if not at least 3 substitions are made, do some later

    ingr_seen = []
    subst_seen = []

    for ingr in ingredients:

        # replace meats with healthier meats
        isMeat = checkMembership(pipe2, ingr.main_comp, 'meat')
        isFish = checkMembership(pipe2, ingr.main_comp, 'fish')
        isFruit = checkMembership(pipe2, ingr.main_comp, 'fruit')
        # 'turkey' in ingr.main_comp
        # 'chicken' in ingr.main_comp
        # print(ingr.main_comp + ": " + str(isMeat))
        # print(ingr.main_comp + ": " + str(isFish))
        if (isMeat > 0.8 or isFish > 0.8) and isFruit < 0.5 and not "water" in ingr.main_comp.lower():
            if "sauce" in ingr.main_comp:
                new_instructions.append("Instead of " + ingr.main_comp + ", use a meatless variant of the sauce. You can use the same amount (" + getQuantityString(ingr, 1) + ").")
                num_subs += 1
            elif "broth" in ingr.main_comp:
                new_instructions.append("Instead of " + ingr.main_comp + ", use a meatless/vegetable broth. You can use the same amount (" + getQuantityString(ingr, 1) + ").")
                num_subs += 1
            else:
                new_instructions.append("Instead of " + ingr.main_comp + ", use either tofu or eggplant. We will default to tofu for fish and eggplant for other meats, but either could be used. You can use the same amount (" + getQuantityString(ingr, 1) + "). These usually take around 20-35 minutes to cook depending on the method, but are likely fine with the original time specified by the recipe.")
                num_subs += 1
            # if isMeat > isFish:
            #     ingr.main_comp = "eggplant"
            # else:
            #     ingr.main_comp = "tofu"
            # continue
        # print(getQuantityString(ingr, 0.5))
        
        # go through healthy ingr subs and do those substitutions
        for hk in veg_ingr_subs.keys():
            if spv2.isDerivativeOfSecond(hk, ingr.main_comp)[1] > 0:
                # different things to say based on if there are mod, sub, or multi tagged suggestions
                # first, sort the diff tag suggestions into different lists
                ingr_seen.append(ingr.main_comp)
                tags = veg_ingr_subs[hk]
                modss = []
                subss = []
                multis = []
                for tt in tags:
                    if tt[1] == "mod":
                        modss.append(tt[0])
                    elif tt[1] == "sub":
                        subss.append(tt[0])
                    elif tt[1] == "multi":
                        multis.append(tt[0])

                ingr_res = ""
                for mm in modss:
                    ingr_res += "You can use a " + mm + " version of " + ingr.main_comp + " instead to make this more vegetarian-friendly. "
                for su in subss:
                    if su in subst_seen:
                        sub_list = get_substitute_list(ingr.main_comp)
                        if sub_list == None: continue
                        sub_list = getNonMeat(sub_list)
                        sub_list = rankHealthy(sub_list)
                        if len(sub_list) < 1: continue
                        counter = 0
                        while counter < len(sub_list) and sub_list[counter].lower() in subst_seen:
                            counter += 1
                        if counter >= len(sub_list): continue
                        ingr_res += "You could substitute " + ingr.main_comp + " with " + sub_list[counter].lower() + ". "
                        subst_seen.append(sub_list[counter].lower())
                        continue
                    ingr_res += "You could substitute " + ingr.main_comp + " with " + su + ". "
                    subst_seen.append(su)
                for mu in multis:
                    if getQuantityString(ingr,1) == "": continue
                    ingr_res += "If you don't want to replace " + ingr.main_comp + ", you could use " + str(mu) + " of the original amount: " + getQuantityString(ingr,1) + " (new amount: " + getQuantityString(ingr, mu) + "). "
                    

                new_instructions.append(ingr_res)
                num_subs += 1
                break

    if num_subs < min_transforms:
        for ingr in ingredients:
            # skip past ingredients we already have a transformation for
            if ingr.main_comp in ingr_seen:
                continue
            # find a substitution for an untransformed ingredient
            # new_sub = getSubList(ingr.main_comp, ["vegetarian"])[0]
            sub_list = get_substitute_list(ingr.main_comp)
            if sub_list == None: continue
            sub_list = getNonMeat(sub_list)
            sub_list = rankHealthy(sub_list)
            if len(sub_list) < 1: continue
            new_instructions.append("You could substitute " + ingr.main_comp + " with " + sub_list[0].lower() + ".")
            # new_instructions.append("You could substitute " + ingr.main_comp + " with " + new_sub.lower() + ".")
            num_subs += 1
            if num_subs >= min_transforms:
                break 

    # for abc in new_instructions:
    #     print(abc)
    return new_instructions

# MAKE NON-VEG

# try to determine main ingredient through matching ingredients to the recipe name. look for common meat substitutes like tofu, eggplant, mushroom, etc. before trying that, as this is more likely to be a good transformation
# once the main ingredient is identified, figure out what meat it should be substituted for. probably default to chicken
# make misc other changes like adding citrus or changing any substitutes to the original thing they are replacing
def makeNonVeg(pipe2, ingredients: list, main_action: str, action_priority_list: list, recipe_name: str):
    new_instructions = []

    min_transforms = 1

    # ingredient word as key to an array of options. this array is made of tuples for suggestions. the 1st (not 0th) element specifies whether it is a quantity mod ('multi'), a substitution ('sub'), or a modded ver ('mod')
    veg_ingr_subs = {'eggplant':[('beef', 'sub')], 'tofu':[('chicken', 'sub')], 'mushrooms':[('pork', 'sub')]}

    # basically, just analyze the steps, ingredients, and main cooking action to see what can be made healthier through IF statements, and maybe webscraped substitutions
    

    # now, go through the ingredients
    num_subs = 0 # counter for the number of substitutions made. if not at least 3 substitions are made, do some later

    ingr_seen = []
    subst_seen = []

    for ingr in ingredients: 
        # go through healthy ingr subs and do those substitutions
        for hk in veg_ingr_subs.keys():
            if spv2.isDerivativeOfSecond(hk, ingr.main_comp)[1] > 0:
                # different things to say based on if there are mod, sub, or multi tagged suggestions
                # first, sort the diff tag suggestions into different lists
                ingr_seen.append(ingr.main_comp)
                tags = veg_ingr_subs[hk]
                modss = []
                subss = []
                multis = []
                for tt in tags:
                    if tt[1] == "mod":
                        modss.append(tt[0])
                    elif tt[1] == "sub":
                        subss.append(tt[0])
                    elif tt[1] == "multi":
                        multis.append(tt[0])

                ingr_res = ""
                for mm in modss:
                    ingr_res += "You can use a " + mm + " version of " + ingr.main_comp + " instead to make this more non-veg. "
                for su in subss:
                    if su in subst_seen:
                        sub_list = get_substitute_list(ingr.main_comp)
                        if sub_list == None: continue
                        sub_list = getMeat(sub_list)
                        sub_list = rankHealthy(sub_list)
                        if len(sub_list) < 1: continue
                        counter = 0
                        while counter < len(sub_list) and sub_list[counter].lower() in subst_seen:
                            counter += 1
                        if counter >= len(sub_list): continue
                        ingr_res += "You could substitute " + ingr.main_comp + " with " + sub_list[counter].lower() + ". "
                        subst_seen.append(sub_list[counter].lower())
                        continue
                    ingr_res += "You could substitute " + ingr.main_comp + " with " + su + ". "
                    subst_seen.append(su)
                for mu in multis:
                    if getQuantityString(ingr,1) == "": continue
                    ingr_res += "If you don't want to replace " + ingr.main_comp + ", you could use " + str(mu) + " of the original amount: " + getQuantityString(ingr, mu) + ". "

                new_instructions.append(ingr_res)
                num_subs += 1
                break

    if num_subs < min_transforms:
        new_instructions.append("Sprinkle bacon bits on top of the finished product.")
        num_subs += 1
        for ingr in ingredients:
            
            if num_subs >= min_transforms:
                break 
            # skip past ingredients we already have a transformation for
            if ingr.main_comp in ingr_seen:
                continue
            # find a substitution for an untransformed ingredient
            # new_sub = getSubList(ingr.main_comp, ["non-veg"])[0]
            sub_list = get_substitute_list(ingr.main_comp)
            if sub_list == None: continue
            sub_list = getMeat(sub_list)
            sub_list = rankHealthy(sub_list)
            if len(sub_list) < 1: continue
            new_instructions.append("You could substitute " + ingr.main_comp + " with " + sub_list[0].lower() + ".")
            # new_instructions.append("You could substitute " + ingr.main_comp + " with " + new_sub.lower() + ".")
            num_subs += 1
            if num_subs >= min_transforms:
                break 

    # for abc in new_instructions:
    #     print(abc)
    return new_instructions

### MAKE INDIAN

# butter -> ghee
# cinnamon, ginger -> cardamom
# citrus -> coriander
# pepper -> tumeric
# add cumin (1/2 tsp)
# sugar -> jaggery powder
# rice -> basmati
# jalapeno -> chilli
# flour -> rice flour
# milk -> coconut milk
# fruit -> tamarind
# beans -> chickpeas
# peas -> chickpeas
def makeInd(pipe2, ingredients: list, main_action: str, action_priority_list: list):
    new_instructions = []

    min_transforms = 3

    # ingredient word as key to an array of options. this array is made of tuples for suggestions. the 1st (not 0th) element specifies whether it is a quantity mod ('multi'), a substitution ('sub'), or a modded ver ('mod')
    ind_ingr_subs = {'butter':[('ghee', 'sub')], 'cinnamon':[('cardamom', 'sub')], 'milk':[('coconut milk', 'sub')], 'ginger':[('cardamom', 'sub')], 'citrus':[('coriander', 'sub')], 'pepper':[('tumeric', 'sub')], 'sugar':[('jaggery powder', 'sub')], 'rice':[('basmati', 'mod')], 'jalapeno':[('chilli pepper', 'sub')],'chilli':[(1.25, 'multi')], 'flour':[('rice flour', 'sub')], 'beans':[('chickpeas', 'sub')], 'peas':[('chickpeas', 'sub')]}

    # basically, just analyze the steps, ingredients, and main cooking action to see what can be made healthier through IF statements, and maybe webscraped substitutions


    # now, go through the ingredients
    num_subs = 0 # counter for the number of substitutions made. if not at least 3 substitions are made, do some later

    ingr_seen = []
    subst_seen = []

    for ingr in ingredients:

        # replace meats with healthier meats
        isFruit = checkMembership(pipe2, ingr.main_comp, 'fruit')
        # 'turkey' in ingr.main_comp
        # 'chicken' in ingr.main_comp
        # print(ingr.main_comp + ": " + str(isMeat))
        # print(ingr.main_comp + ": " + str(isFish))
        if isFruit > 0.8:
            new_instructions.append("Instead of " + ingr.main_comp + ", use tamarind. You can use the same amount (" + getQuantityString(ingr, 1) + ").")
            num_subs += 1
            # ingr.main_comp = "tamarind"
            
            continue
        # print(getQuantityString(ingr, 0.5))
        
        # go through healthy ingr subs and do those substitutions
        for hk in ind_ingr_subs.keys():
            if spv2.isDerivativeOfSecond(hk, ingr.main_comp)[1] > 0:
                # different things to say based on if there are mod, sub, or multi tagged suggestions
                # first, sort the diff tag suggestions into different lists
                ingr_seen.append(ingr.main_comp)
                tags = ind_ingr_subs[hk]
                modss = []
                subss = []
                multis = []
                for tt in tags:
                    if tt[1] == "mod":
                        modss.append(tt[0])
                    elif tt[1] == "sub":
                        subss.append(tt[0])
                    elif tt[1] == "multi":
                        multis.append(tt[0])

                ingr_res = ""
                for mm in modss:
                    ingr_res += "You can use a " + mm + " version of " + ingr.main_comp + " instead to make this more Indian. "
                for su in subss:
                    if su in subst_seen:
                        continue
                    ingr_res += "You could substitute " + ingr.main_comp + " with " + su + ". "
                    subst_seen.append(su)
                for mu in multis:
                    if getQuantityString(ingr,1) == "": continue
                    ingr_res += "If you don't want to replace " + ingr.main_comp + ", you could use " + str(mu) + " of the original amount: "  + getQuantityString(ingr,1) + " (new amount: " + getQuantityString(ingr, mu) + "). "

                new_instructions.append(ingr_res)
                num_subs += 1
                break

    if num_subs < min_transforms:
        for ingr in ingredients:
            # skip past ingredients we already have a transformation for
            if ingr.main_comp in ingr_seen:
                continue
            # find a substitution for an untransformed ingredient
            # new_sub = getSubList(ingr.main_comp, ["indian"])[0]
            sub_list = get_substitute_list(ingr.main_comp)
            if sub_list == None: continue
            # sub_list = getNonMeat(sub_list)
            sub_list = rankHealthy(sub_list)
            if len(sub_list) < 1: continue
            new_instructions.append("You could substitute " + ingr.main_comp + " with " + sub_list[0].lower() + ".")
            # new_instructions.append("You could substitute " + ingr.main_comp + " with " + new_sub.lower() + ".")
            num_subs += 1
            if num_subs >= min_transforms:
                break 

    # for abc in new_instructions:
    #     print(abc)
    return new_instructions

# makeInd(ingredients, main_action, action_priority_list)

### CHANGE PORTIONS
def getNewPortions(pipe2, ingredients:list, multiplier: float):
    new_ingr = []
    for ingr in ingredients:
        newQ = None
        newSQ = None
        if ingr.quantity != None:
            newQ = str(floatFromFractionString(ingr.quantity) * multiplier)
        if ingr.quantity == None and ingr.sub_quantity != None:
            newSQ = str(floatFromFractionString(ingr.sub_quantity) * multiplier)
        elif ingr.sub_quantity != None:
            newSQ = ingr.sub_quantity
        new_ingr.append(ingredients_parser.Ingredient(ingr.og_text, ingr.main_comp, newQ, ingr.measurement, newSQ, ingr.sub_measurement, ingr.descriptors))

    # for ni in new_ingr:
    #     print(ni)

    return new_ingr

### DAIRY FREE


def makeDairyFree(pipe2, ingredients: list, main_action: str, action_priority_list: list):
    new_instructions = []

    dairy_keywords = ['milk', 'cream', 'cheese', 'half & half', 'half and half', 'butter', 'whey', 'lactose', 'yogurt', 'chocolate']

    # now, go through the ingredients

    for ingr in ingredients:
        for hk in dairy_keywords:
            if hk in ingr.main_comp:
                
                if hk in ['cream', 'half & half', 'half and half']:
                    ingr_res = "You could substitute " + ingr.main_comp + " with coconut cream. "
                    new_instructions.append(ingr_res)
                    break
                elif hk == "whey":
                    ingr_res = "You could substitute " + ingr.main_comp + " with rice protein. "
                    new_instructions.append(ingr_res)
                    break
                elif hk == "chocolate":
                    ingr_res = "You could use a dark chocolate version of " + ingr.main_comp + " instead."
                    new_instructions.append(ingr_res)
                    break

                sub_list = get_substitute_list(ingr.main_comp)
                if sub_list == None: continue
                sub_list = getDairyFree(sub_list)
                if len(sub_list) < 1: continue
                sub_list = rankHealthy(sub_list)

                ingr_res = "You could substitute " + ingr.main_comp + " with " + sub_list[0] + ". "

                new_instructions.append(ingr_res)
                break

    # for abc in new_instructions:
    #     print(abc)
    return new_instructions

### GLUTEN FREE


def makeGlutenFree(pipe2, ingredients: list, main_action: str, action_priority_list: list):
    new_instructions = []

    gluten_keywords = ['wheat', 'flour', 'rye', 'barley', 'malt', 'starch', 'pasta', 'spaghetti', 'ravioli', 'dumpling', 'ramen', 'soba', 'udon', 'bread', 'tortilla', 'crumb', 'toast', 
                       'beer', 'pita', 'oats', 'oatmeal', 'bagel', 'muffin', 'naan', 'biscuit', 'roux', 'noodle']

    # now, go through the ingredients

    for ingr in ingredients:
        for hk in gluten_keywords:
            if hk in ingr.main_comp:
                
                sub_list = get_substitute_list(ingr.main_comp)
                if sub_list == None: continue
                sub_list = getGlutenFree(sub_list)
                if len(sub_list) < 1: continue
                sub_list = rankHealthy(sub_list)

                ingr_res = "You could substitute " + ingr.main_comp + " with " + sub_list[0] + ". "

                new_instructions.append(ingr_res)
                break

    # for abc in new_instructions:
    #     print(abc)
    return new_instructions