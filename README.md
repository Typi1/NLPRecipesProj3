# MealMaster

By:
    Gustavo Carvalho
    Sean Lee
    Ethan Kim

## 1) Description
MealMaster is a simple recipe transformation and reference tool. Given a provided recipe, here are the following ways MealMaster can help you:

1. Can print out the ingredient list
2. Can print out the list of tools and kitchen appliances required for the recipe
3. Can print out the list of steps
4. Can give instructions on how to transform the recipe to vegetarian/non-vegetarian
5. Can give instructions on how to transform the recipe to be more/less healthy
6. Can give instructions on how to make the recipe more like Indian cuisine
7. Can give a modified ingredient list for the recipe with the quantities all multiplied by a given value (ex: make 1.5x the original amount)
8. Can make the recipe lactose-free or gluten-free

## 2) How to use the program

	- A few preliminary notes:
		- Sometimes, the program will ask you to "Input anything to continue." If you just press Enter, you can proceed with the program. This intermediary step is primarily so that the output of the previous action isn't immediately pushed too far up by the next prompt text.
		- Transformations will not carry over across different transformation attempts:
			- For example, doubling the amount of ingredients and then making the recipe vegetarian will not then print out a vegetarian version of the recipe with double the ingredients, just a vegetarian version of the recipe since the multiplier isn't saved.
				- This is primarily to allow the user to try different transformations on the original recipe without making it unrecognizable through countless transformations, and so it is easier to cross-reference with the original recipe text.
			

	- First, run the file MealMasterProj3.py to start the program.
	- Upon loading, MealMaster will ask you to give it a URL from allrecipes.com. Paste or type a valid URL and press Enter.
	- It will then process the recipe. This may take a couple minutes. There will be a clear message indicating when it is done processing ("Alright, [recipe_name] has been booted up!").
	- From here, you can choose to do multiple actions from a MAIN ACTION HUB.

#	- MAIN ACTION HUB
		- If you type in "1" and then press Enter, MealMaster will provide the ingredients as given in the recipe.
		- If you type in "2" and then press Enter, MealMaster will provide a list of tools and kitchen appliances needed for the recipe.
		- If you type in "3" and then press Enter, MealMaster will provide a list of all the steps as given in the recipe.
		- If you type in "5" and then press Enter, MealMaster will print out a human-readable version of our parsed ingredients data structure for grading reference.
		- If you type in "6" and then press Enter, MealMaster will print out a human-readable version of our parsed steps data structure for grading reference.
		- If you type in "7" and then press Enter, MealMaster will ask you whether you want to exit the program. 
			- If you reply "yes", it will end the program. 
			- If you reply, "no", it will continue back to MAIN ACTION HUB.
		- If you type in "4" and then press Enter, MealMaster will take you to an option select for what kind of transformation you want to apply to the recipe (see TRANSFORMATION HUB).
		
		- If the action performed isn't the ones indicated by '4' or '7', the program will return to MAIN ACTION HUB after.

#	- TRANSFORMATION HUB	
		- If you type in "1" and then press Enter, MealMaster will print a list of actions one could take to make the recipe vegetarian-friendly.
		- If you type in "2" and then press Enter, MealMaster will print a list of actions one could take to make the recipe non-vegetarian.
		- If you type in "3" and then press Enter, MealMaster will print a list of actions one could take to make the recipe healthier.
		- If you type in "4" and then press Enter, MealMaster will print a list of actions one could take to make the recipe less healthy.
		- If you type in "5" and then press Enter, MealMaster will print a list of actions one could take to make the recipe more like Indian cuisine.
		- If you type in "6" and then press Enter, MealMaster will ask you to type a number in decimal form that will be the multiplier of how much more/less you want of the recipe. 
			- For example, "2" would double the ingredients used in the recipe, and "0.5" would half the ingredients used in the recipe.
			- After typing in the number and pressing Enter, a modified version of our ingredients data structure will be printed with the quantities changed by the given amount.
		- If you type in "7" and then press Enter, MealMaster will print a list of actions one could take to make the recipe lactose-free.
		- If you type in "8" and then press Enter, MealMaster will print a list of actions one could take to make the recipe gluten free.
		- If you type in "9" and then press Enter, MealMaster will go back to MAIN ACTION HUB.

		- Note that after any action from the TRANSFORMATION HUB that isn't '9', a prompt will appear asking one to choose if they want to perform a different transformation or if they are done with transformations.
			- If you type in '1' and then press Enter, MealMaster will take you back to TRANSFORMATION HUB.
			- If you type in '2' and then press Enter, MealMaster will take you back to MAIN ACTION HUB.
				- This may be useful if you want to see the original ingredients and/or recipe steps.
		

## 3) Which Recipes MealMaster Can Use

You can give MealMaster any url from allrecipes.com

Any other recipe website is not guaranteed to work.


## 4) Installation
1. Download the github repo or zip file from Canvas
2. Install all packages by running $ pip install -r requirements. txt
3. Run the file MealMasterProj3.py to start the bot! 

REQUIRES Python 3.10 OR LATER TO RUN

Github repository: https://github.com/Typi1/NLPRecipesProj3
