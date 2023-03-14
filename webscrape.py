from bs4 import BeautifulSoup
import json
import requests

def get_soup(url:str):
    response = requests.get(url)
    return BeautifulSoup(response.text, "html.parser")

def get_dict(url:str):
    recipe_html = get_soup(url)
    recipe_dict = None
    d_type = None
    candidate_json = recipe_html.find_all("script", {"type": "application/ld+json"})
    for candidate in candidate_json:
        r = json.loads(candidate.text)
        # print(type(r))
        if isinstance(r, dict):
            if r["@type"] == "Recipe":
                recipe_dict = r
                d_type = dict
                break
        elif isinstance(r, list):
            if r[0]["@type"][0] == "Recipe":
                recipe_dict = r
                d_type = list
                break
            elif r[0]["@type"] == "Recipe":
                recipe_dict = r
                d_type = list
                break
    return [recipe_dict, d_type]

def get_recipe(url:str):
    recipe = get_dict(url)
    # print(recipe)
    if recipe[0]:
        if recipe[1] == dict:
            ingredients = recipe[0]["recipeIngredient"]
            if "itemListElement" in recipe[0]["recipeInstructions"]:
                steps = recipe[0]["recipeInstructions"]["itemListElement"]
            else:
                steps = recipe[0]["recipeInstructions"]
        elif recipe[1] == list:
            ingredients = recipe[0][0]["recipeIngredient"]
            if "itemListElement" in recipe[0][0]["recipeInstructions"][0]:
                steps = recipe[0][0]["recipeInstructions"][0]["itemListElement"]
            else:
                steps = recipe[0][0]["recipeInstructions"]
    instructions = []
    for step in steps:
        if "text" in step:
            instructions.append(step["text"])
    print(ingredients)
    print(instructions)
    return [ingredients, instructions]

def main():
    url = 'https://www.allrecipes.com/recipe/16167/beef-bourguignon-i/'
    get_recipe(url)

if __name__ == "__main__":
    main()

# https://www.allrecipes.com/recipe/10813/best-chocolate-chip-cookies/
# https://www.allrecipes.com/recipe/24074/alysias-basic-meat-lasagna/
# https://www.allrecipes.com/recipe/244716/shirataki-meatless-meat-pad-thai/
# https://www.allrecipes.com/recipe/16167/beef-bourguignon-i/
# https://www.allrecipes.com/recipe/228285/teriyaki-salmon/
# https://www.allrecipes.com/recipe/229293/korean-saewoo-bokkeumbap-shrimp-fried-rice/
# https://www.allrecipes.com/recipe/7757/tiramisu-cheesecake/
# https://www.allrecipes.com/recipe/73303/mexican-rice-iii/