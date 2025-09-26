# ------------------------------
# Imports
# ------------------------------
import streamlit as st
import pandas as pd
import numpy as np

# ------------------------------
# Load data
# ------------------------------
full_data_ingredients = pd.read_csv('Herbal ingredients - Sheet1 (4).csv')
full_data_ingredients = full_data_ingredients.rename(
    columns={'Unnamed: 5': 'Description',
             'Rarity (1-10), Description': 'Rarity'}
)

# ------------------------------
# Helper function: get_id
# ------------------------------
def get_id(value):
    if value in full_data_ingredients['id'].values:
        return value
    rows = full_data_ingredients[full_data_ingredients['Common Name'] == value]
    if not rows.empty:
        return rows.iloc[0]['id']
    return None

# ------------------------------
# Ingredient effect calculation
# ------------------------------
def ingredient_effect_count(a, b, c, d):
    cols = ['Anti-Inflammatory', 'Irritation', 'sleep / relaxation',
            'digestive', 'antiseptic / Imunity', 'cardiovascular',
            'cough / throat', 'cognitive / nerve (rare)', 'Depression (rare)']
    sums = {cname: 0 for cname in cols}

    Topical = 0
    for item in [a, b, c, d]:
        row = full_data_ingredients[full_data_ingredients['id'] == item]
        if not row.empty and row.iloc[0]['Common Name'] == 'Beeswax':
            Topical = 1
            break

    def safe_item_by_name(name):
        row = full_data_ingredients[full_data_ingredients['Common Name'] == name]
        return row.iloc[0]['id'] if not row.empty else None

    Empty = safe_item_by_name('Empty')
    Alcohol_id = safe_item_by_name('Alcohol')
    Carrier_id = safe_item_by_name('Carrier Oils')
    Beeswax_id = safe_item_by_name('Beeswax')
    Glycerin_id = safe_item_by_name('Glycerin')

    mult = 1.0
    result_list = []

    for item in [a, b, c, d]:
        row = full_data_ingredients[full_data_ingredients['id'] == item]
        applied_topically = False
        if not row.empty:
            val = row.iloc[0]['applied topically? ']
            applied_topically = str(val).strip().lower() in ('1','true','yes','y','t')

        if applied_topically and Topical != 1:
            new_item = Empty
            result_list.append(new_item)
            continue

        if item == Alcohol_id:
            mult += 1.0
            new_item = Empty
        elif item == Carrier_id:
            new_item = Empty
            if Topical == 1:
                mult += 0.5
        elif item == Beeswax_id:
            new_item = Empty
        elif item == Glycerin_id:
            mult += 1.0
            new_item = Empty
        else:
            new_item = item

        result_list.append(new_item)

    for ingr in result_list:
        row = full_data_ingredients[full_data_ingredients['id'] == ingr]
        if row.empty:
            continue
        for cname in cols:
            try:
                sums[cname] += int(row.iloc[0][cname])
            except Exception:
                sums[cname] += 0

    effects_array = np.array([sums[cname] for cname in cols] + [Topical], dtype=float)
    effects_array *= mult
    return effects_array

# ------------------------------
# Potion strength table
# ------------------------------
potions_strengths_total = pd.DataFrame({
    'label': ['Weak', 'Normal', 'Strong', 'Extreme'],
    'value': np.array([0.25, 0.55, 0.80, 1.0])
})

# ------------------------------
# Potion effect chance
# ------------------------------
def Potion_chance(ingredient_effect_list, rare_mult):
    ingredient_effects = np.delete(ingredient_effect_list, -1)  # remove Topical flag
    effect_array = np.array([effect * rare_mult if i >= 7 else effect
                             for i, effect in enumerate(ingredient_effects)])
    total = np.sum(effect_array)
    if total == 0:
        return "Potion fizzles... no effect"

    prob = effect_array / total
    chosen_index = np.random.choice(len(effect_array), p=prob)
    strength = effect_array[chosen_index] / np.max(effect_array)

    effect_names = [
        "Anti-Inflammatory", "Irritation", "Sleep/Relaxation", "Digestive",
        "Antiseptic/Immunity", "Cardiovascular", "Cough/Throat",
        "Cognitive/Nerve", "Depression"
    ]

    label = potions_strengths_total[potions_strengths_total['value'] >= strength].iloc[0]['label']

    return {
        "effect": effect_names[chosen_index],
        "strength": round(strength, 2),
        "strength_label": label,
        "raw_value": effect_array[chosen_index],
        "probability": round(prob[chosen_index], 2)
    }

# ------------------------------
# Streamlit UI
# ------------------------------
st.title("Potion Maker 🧪")

# Dropdowns to select ingredients
ingredient_options = full_data_ingredients['Common Name'].tolist()
ing1 = st.selectbox("Ingredient 1", ingredient_options)
ing2 = st.selectbox("Ingredient 2", ingredient_options)
ing3 = st.selectbox("Ingredient 3", ingredient_options)
ing4 = st.selectbox("Ingredient 4", ingredient_options)

rare_mult = st.slider("Rare Effect Multiplier", min_value=1.0, max_value=3.0, value=1.0, step=0.1)

if st.button("Brew Potion!"):
    effects = ingredient_effect_count(get_id(ing1), get_id(ing2), get_id(ing3), get_id(ing4))
    result = Potion_chance(effects, rare_mult)
    st.subheader("Potion Result")
    st.write(result)
