from pydantic import BaseModel, Field
from typing import List
import json
from anthropic import Anthropic

class Ingredient(BaseModel):
    name: str = Field(description="Ingredient name")
    quantity: str = Field(description="Quantity of the ingredient")
    unit: str = Field(description="Unit of measurement")

class PreparationStep(BaseModel):
    step_number: int = Field(description="Step number")
    description: str = Field(description="Description of the step")

class Recipe(BaseModel):
    title: str = Field(description="Recipe title")
    prep_time: str = Field(description="Preparation time")
    difficulty: str = Field(description="Difficulty level")
    ingredients: List[Ingredient] = Field(description="List of ingredients")
    steps: List[PreparationStep] = Field(description="Preparation steps")
    notes: str = Field(description="Additional notes or suggestions")

class RecipeAgent:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-7-sonnet-20250219"

    def generate_recipes(self, fridge_ingredients: str) -> List[Recipe]:
        prompt = f"""
You have the following ingredients: {fridge_ingredients}

Generate THREE distinct recipes using these ingredients. Each recipe should be different in cuisine or type (appetizer, main course, dessert).
Assume basic pantry items (salt, pepper, oil) are available.

Return the response as JSON with this structure:

{{
  "recipes": [
    {{
      "title": "Recipe 1",
      "prep_time": "e.g. 30 minutes",
      "difficulty": "easy/medium/hard",
      "ingredients": [
        {{ "name": "ingredient1", "quantity": "number", "unit": "e.g. grams, pieces, tbsp" }},
        ...
      ],
      "steps": [
        {{ "step_number": 1, "description": "First step" }},
        ...
      ],
      "notes": "Additional notes"
    }},
    ...
  ]
}}
"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        text = response.content[0].text
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        json_str = text[json_start:json_end]

        data = json.loads(json_str)
        recipes = [Recipe(**r) for r in data.get("recipes", [])]
        return recipes