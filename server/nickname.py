import random

positive_adjectives = ["acclaimed", "accomplished", "accurate", "admirable", "adorable", "adored", "advanced",
                       "adventurous", "affectionate", "agile", "agreeable", "altruistic", "amazing", "ambitious",
                       "ample", "amusing", "angelic", "appropriate", "astonishing", "attentive", "attractive",
                       "authentic", "awesome", "beautiful", "beloved", "beneficial", "best", "better", "blissful",
                       "bountiful", "brave", "bright", "brilliant", "brisk", "buoyant", "calm", "carefree",
                       "celebrated", "charming", "cheerful", "cheery", "classic", "clean", "clear", "clear-cut",
                       "clever", "colorful", "comfortable", "compassionate", "considerate", "cool", "cooperative",
                       "courageous", "courteous", "creative", "crisp", "cute", "daring", "darling", "dazzling",
                       "decent", "decisive", "delectable", "delicious", "delightful", "dependable", "diligent",
                       "eager", "earnest", "easy", "ecstatic", "educated", "elated", "elegant", "eminent",
                       "enchanted", "enchanting", "energetic", "envious", "ethical", "euphoric", "everlasting",
                       "exalted", "excellent", "excited", "exciting", "exemplary", "fabulous", "fair", "faithful",
                       "famous", "fancy", "fantastic", "fast", "favorable", "favorite", "fearless", "feisty", "fine",
                       "flashy", "flawless", "fond", "fortunate", "fragrant", "free", "fresh", "friendly", "frugal",
                       "fruitful", "generous", "gentle", "genuine", "gifted", "glamorous", "gleeful", "glistening",
                       "glorious", "golden", "good", "gorgeous", "graceful", "gracious", "grand", "grateful", "great",
                       "handsome", "handy", "happy", "harmless", "harmonious", "healthy", "heartfelt", "heavenly",
                       "helpful", "hilarious", "honest", "honorable", "honored", "hopeful", "hospitable", "hot",
                       "humble", "ideal", "idolized", "illustrious", "imaginative", "immaculate", "immense",
                       "impartial", "impassioned", "impeccable", "important", "impressive", "incredible",
                       "instructive", "intelligent", "interesting", "jolly", "jovial", "joyful", "joyous", "jubilant",
                       "judicious", "keen", "kindly", "knowledgeable", "lavish", "lawful", "leading", "lean",
                       "likable", "lively", "lovable", "lovely", "loving", "loyal", "lucky", "luminous", "lustrous",
                       "luxurious", "magnificent", "majestic", "marvelous", "mature", "memorable", "merry", "modern",
                       "modest", "monumental", "neat", "nice", "nifty", "nimble", "noteworthy", "optimal",
                       "optimistic", "opulent", "orderly", "outstanding", "overjoyed", "passionate", "peaceful",
                       "perfect", "playful", "pleasant", "pleased", "pleasing", "plush", "poised", "polished",
                       "polite", "popular", "posh", "positive", "powerful", "precious", "prestigious", "pretty",
                       "prize", "productive", "profuse", "proper", "proud", "prudent", "punctual", "pure", "quaint",
                       "qualified", "quiet", "radiant", "rapid", "ready", "realistic", "reasonable", "regal",
                       "reliable", "remarkable", "respectful", "rewarding", "rich", "right", "robust", "rosy",
                       "safe", "sane", "satisfied", "serene", "sharp", "shimmering", "shiny", "silent", "smart",
                       "smooth", "snappy", "sociable", "soft", "solid", "sophisticated", "soulful", "sparkling",
                       "spectacular", "speedy", "spirited", "splendid", "spotless", "stable", "stimulating",
                       "striking", "strong", "stunning", "stupendous", "sturdy", "stylish", "super", "superb",
                       "superior", "supportive", "sweet", "swift", "tempting", "tender", "terrific", "thankful",
                       "thoughtful", "thrifty", "tidy", "timely", "tough", "trusting", "trustworthy", "trusty",
                       "truthful", "unselfish", "upbeat", "usable", "useful", "valuable", "verifiable", "vibrant",
                       "victorious", "vigilant", "virtuous", "vivacious", "vivid", "warm", "warmhearted", "wealthy",
                       "welcome", "well-informed", "well-made", "willing", "wise", "witty", "wonderful", "worthwhile",
                       "worthy", "youthful"]

animals = ["Hedgehog", "Crab", "Bald eagle", "Reindeer", "Mouse", "Robin", "Leopard", "Alligator", "Koala", "Rabbit",
           "Woodpecker", "Panda", "Peacock", "Duck", "Lion", "Turtle", "Goldfish", "Elk", "Bat", "Hare", "Lizard",
           "Camel", "Bee", "Stork", "Badger", "Raven", "Penguin", "Giraffe", "Squirrel", "Tiger", "Owl", "Fox", "Dove",
           "Deer", "Shrimp", "Hamster", "Sparrow", "Kangaroo", "Hedgehog", "Parrot", "Ostrich", "Crocodile",
           "Dolphin", "Otter", "Flamingo", "Ox", "Goose", "Chicken", "Swallow", "Hawk", "Swan"]


def get_new_name():
    a = positive_adjectives[random.randint(0, len(positive_adjectives) - 1)]
    b = positive_adjectives[random.randint(0, len(positive_adjectives) - 1)]
    return f"{a} {b}"
