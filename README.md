# Recipe Agent

Agent generujący przepisy kulinarne na podstawie składników dostępnych w lodówce.

## Opis

Ten agent wykorzystuje model Claude od Anthropic do generowania trzech różnych przepisów kulinarnych na podstawie podanych składników.

## Użycie

```python
from recipe_agent import RecipeAgent

agent = RecipeAgent(api_key="YOUR_ANTHROPIC_API_KEY")
recipes = agent.generate_recipes("eggs, milk, flour, sugar")

for recipe in recipes:
    print(recipe.title)
    for ingredient in recipe.ingredients:
        print(f"- {ingredient.quantity} {ingredient.unit} {ingredient.name}")
    for step in recipe.steps:
        print(f"{step.step_number}. {step.description}")# RecipeAgent
