import random

positive_adjectives = ["Acclaimed", "Accomplished", "Accurate", "Admirable", "Adorable", "Adored", "Advanced",
                       "Adventurous", "Affectionate", "Agile", "Agreeable", "Altruistic", "Amazing", "Ambitious",
                       "Ample", "Amusing", "Angelic", "Appropriate", "Astonishing", "Attentive", "Attractive",
                       "Authentic", "Awesome", "Beautiful", "Beloved", "Beneficial", "Best", "Better", "Blissful",
                       "Bountiful", "Brave", "Bright", "Brilliant", "Brisk", "Buoyant", "Calm", "Carefree",
                       "Celebrated", "Charming", "Cheerful", "Cheery", "Classic", "Clean", "Clear", "Clear-cut",
                       "Clever", "Colorful", "Comfortable", "Compassionate", "Considerate", "Cool", "Cooperative",
                       "Courageous", "Courteous", "Creative", "Crisp", "Cute", "Daring", "Darling", "Dazzling",
                       "Decent", "Decisive", "Delectable", "Delicious", "Delightful", "Dependable", "Diligent",
                       "Eager", "Earnest", "Ecstatic", "Educated", "Elated", "Elegant", "Eminent",
                       "Enchanted", "Enchanting", "Energetic", "Envious", "Ethical", "Euphoric", "Everlasting",
                       "Exalted", "Excellent", "Excited", "Exciting", "Exemplary", "Fabulous", "Fair", "Faithful",
                       "Famous", "Fancy", "Fantastic", "Fast", "Favorable", "Favorite", "Fearless", "Feisty", "Fine",
                       "Flashy", "Flawless", "Fond", "Fortunate", "Fragrant", "Free", "Fresh", "Friendly", "Frugal",
                       "Fruitful", "Generous", "Gentle", "Genuine", "Gifted", "Glamorous", "Gleeful", "Glistening",
                       "Glorious", "Golden", "Good", "Gorgeous", "Graceful", "Gracious", "Grand", "Grateful", "Great",
                       "Handsome", "Handy", "Happy", "Harmless", "Harmonious", "Healthy", "Heartfelt", "Heavenly",
                       "Helpful", "Hilarious", "Honest", "Honorable", "Honored", "Hopeful", "Hospitable", "Hot",
                       "Humble", "Ideal", "Idolized", "Illustrious", "Imaginative", "Immaculate", "Immense",
                       "Impartial", "Impassioned", "Impeccable", "Important", "Impressive", "Incredible",
                       "Instructive", "Intelligent", "Interesting", "Jolly", "Jovial", "Joyful", "Joyous", "Jubilant",
                       "Judicious", "Keen", "Kindly", "Knowledgeable", "Lavish", "Lawful", "Leading", "Lean",
                       "Likable", "Lively", "Lovable", "Lovely", "Loving", "Loyal", "Lucky", "Luminous", "Lustrous",
                       "Luxurious", "Magnificent", "Majestic", "Marvelous", "Mature", "Memorable", "Merry", "Modern",
                       "Modest", "Monumental", "Neat", "Nice", "Nifty", "Nimble", "Noteworthy", "Optimal",
                       "Optimistic", "Opulent", "Orderly", "Outstanding", "Overjoyed", "Passionate", "Peaceful",
                       "Perfect", "Playful", "Pleasant", "Plush", "Poised", "Polished",
                       "Polite", "Popular", "Posh", "Positive", "Powerful", "Precious", "Prestigious", "Pretty",
                       "Prize", "Productive", "Profuse", "Proper", "Proud", "Prudent", "Punctual", "Pure", "Quaint",
                       "Qualified", "Quiet", "Radiant", "Rapid", "Realistic", "Reasonable", "Regal",
                       "Reliable", "Remarkable", "Respectful", "Rewarding", "Rich", "Right", "Robust", "Rosy",
                       "Safe", "Sane", "Satisfied", "Serene", "Sharp", "Shimmering", "Shiny", "Silent", "Smart",
                       "Smooth", "Snappy", "Sociable", "Soft", "Solid", "Sophisticated", "Soulful", "Sparkling",
                       "Spectacular", "Speedy", "Spirited", "Splendid", "Spotless", "Stable", "Stimulating",
                       "Striking", "Strong", "Stunning", "Stupendous", "Sturdy", "Stylish", "Super", "Superb",
                       "Superior", "Supportive", "Sweet", "Swift", "Tempting", "Tender", "Terrific", "Thankful",
                       "Thoughtful", "Thrifty", "Tidy", "Timely", "Tough", "Trusting", "Trustworthy", "Trusty",
                       "Truthful", "Unselfish", "Upbeat", "Usable", "Useful", "Valuable", "Verifiable", "Vibrant",
                       "Victorious", "Vigilant", "Virtuous", "Vivacious", "Vivid", "Warm", "Warmhearted", "Wealthy",
                       "Welcome", "Well-informed", "Well-made", "Wise", "Witty", "Wonderful", "Worthwhile",
                       "Worthy", "Youthful"]

animals = ["Hedgehog", "Crab", "Eagle", "Reindeer", "Mouse", "Robin", "Leopard", "Alligator", "Koala", "Rabbit",
           "Woodpecker", "Panda", "Peacock", "Duck", "Lion", "Turtle", "Goldfish", "Elk", "Bat", "Hare", "Lizard",
           "Camel", "Bee", "Stork", "Badger", "Raven", "Penguin", "Giraffe", "Squirrel", "Tiger", "Owl", "Fox", "Dove",
           "Deer", "Shrimp", "Hamster", "Sparrow", "Kangaroo", "Hedgehog", "Parrot", "Ostrich", "Crocodile",
           "Dolphin", "Otter", "Flamingo", "Ox", "Goose", "Chicken", "Swallow", "Hawk", "Swan"]


def get_new_name():
    a = positive_adjectives[random.randint(0, len(positive_adjectives) - 1)]
    b = animals[random.randint(0, len(animals) - 1)]
    return f"{a} {b}".title()
