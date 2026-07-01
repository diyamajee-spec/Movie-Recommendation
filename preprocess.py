import os
import sqlite3
import re
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

def clean_title(title):
    """
    Remove trailing release year from movie titles, e.g., 'Toy Story (1995)' -> 'Toy Story'
    """
    if not title:
        return ""
    # Strip any trailing year in parenthesis (e.g. (1995))
    return re.sub(r'\s*\(\d{4}\)\s*$', '', title).strip()

def map_genres(genres_str):
    """
    Clean and map genres to the 18 standard genres:
    Action, Adventure, Animation, Comedy, Crime, Drama, Fantasy, Family,
    History, Horror, Music, Mystery, Romance, Science Fiction, Thriller,
    War, Western, Documentary
    """
    if not genres_str:
        return "Drama"  # Default fallback
        
    # Mapping table for non-standard genres
    genre_mapping = {
        'children': 'Family',
        'musical': 'Music',
        'sci-fi': 'Science Fiction',
        'biography': 'Drama',
        'sports': 'Drama',
        'sport': 'Drama',
        'noir': 'Thriller',
        'film-noir': 'Thriller',
        'imax': 'Action'
    }
    
    # Supported genres list
    supported_genres = {
        'Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Drama', 
        'Fantasy', 'Family', 'History', 'Horror', 'Music', 'Mystery', 
        'Romance', 'Science Fiction', 'Thriller', 'War', 'Western', 'Documentary'
    }
    
    mapped = set()
    raw_genres = [g.strip() for g in genres_str.replace('|', ',').split(',')]
    
    for rg in raw_genres:
        rg_lower = rg.lower()
        if rg_lower in genre_mapping:
            mapped.add(genre_mapping[rg_lower])
        elif rg in supported_genres:
            mapped.add(rg)
        else:
            # Check if any supported genre is a substring of the raw genre
            matched = False
            for sg in supported_genres:
                if sg.lower() in rg_lower:
                    mapped.add(sg)
                    matched = True
                    break
            if not matched:
                # If it's completely unmapped, default to Drama
                mapped.add('Drama')
                
    if not mapped:
        return "Drama"
        
    return ", ".join(sorted(list(mapped)))

# Rich list of curated Bollywood (Hindi), Tamil, and Telugu movies to inject
INDIAN_MOVIES = [
    # --- HINDI (Bollywood) ---
    {
        "Movie Title": "3 Idiots",
        "Genres": "Comedy, Drama",
        "Overview": "Two college friends embark on a road trip journey to find their long-lost companion, Rancho. They revisit their engineering college days, recalling Rancho's inspiring philosophy of learning, passion, and thinking differently, which challenged the rigid academic system and left a lasting impact on their lives.",
        "Language": "hi",
        "Release Year": 2009,
        "Vote Average": 8.4,
        "Poster URL": "https://image.tmdb.org/t/p/w500/w9gTA3Wn0Y5bT0x6t0QhJtH0aL.jpg",
        "Popularity": 95.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Dangal",
        "Genres": "Action, Drama, Family",
        "Overview": "The extraordinary true story of Mahavir Singh Phogat, a former amateur wrestler who dreams of winning a gold medal for India. Unable to do so, he decides to train his two daughters, Geeta and Babita, in the male-dominated sport of wrestling, overcoming societal prejudice and rigid traditions to lead them to international victory.",
        "Language": "hi",
        "Release Year": 2016,
        "Vote Average": 8.0,
        "Poster URL": "https://image.tmdb.org/t/p/w500/7c9P2kosZw96gEkzX0zG5YLOoa7.jpg",
        "Popularity": 92.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Sholay",
        "Genres": "Action, Adventure, Comedy",
        "Overview": "In the small village of Ramgarh, a retired police officer hires two colorful ex-convicts and small-time thieves, Veeru and Jai, to capture the ruthless bandit Gabbar Singh. Gabbar has terrorized the region and brutally massacred the officer's entire family, setting the stage for an epic battle of vengeance and honor.",
        "Language": "hi",
        "Release Year": 1975,
        "Vote Average": 8.2,
        "Poster URL": "https://image.tmdb.org/t/p/w500/2LgP5RntUjCagWvVwM57Gk3j1jV.jpg",
        "Popularity": 88.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Lagaan",
        "Genres": "Drama, History, Romance",
        "Overview": "In Victorian India, the residents of a small village oppressed by high taxes stake their future on a high-stakes game of cricket against their arrogant British rulers. Led by the courageous Bhuvan, the villagers must learn the alien sport from scratch to win a three-year tax exemption or face ruin.",
        "Language": "hi",
        "Release Year": 2001,
        "Vote Average": 7.8,
        "Poster URL": "https://image.tmdb.org/t/p/w500/8b8f2c2tN20cWkX4zM53Gk3j1jV.jpg",
        "Popularity": 85.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Taare Zameen Par",
        "Genres": "Drama, Family",
        "Overview": "Ishaan is an eight-year-old boy who struggles in school and is sent to a boarding boarding school due to his poor academic performance. There, an unconventional and empathetic art teacher, Ram Shankar Nikumbh, discovers Ishaan's artistic brilliance and realizes he has dyslexia, helping him uncover his true potential.",
        "Language": "hi",
        "Release Year": 2007,
        "Vote Average": 8.3,
        "Poster URL": "https://image.tmdb.org/t/p/w500/7t9P2kosZw96gEkzX0zG5YLOoa7.jpg",
        "Popularity": 90.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Bhootnath",
        "Genres": "Comedy, Family, Fantasy",
        "Overview": "A young boy named Banku moves into a massive old villa with his mother, only to discover that it is haunted by a grumpy, resident ghost. Instead of running away in fear, Banku befriends the spirit, forming a heartwarming bond that helps the ghost resolve his past regrets and find peace.",
        "Language": "hi",
        "Release Year": 2008,
        "Vote Average": 6.8,
        "Poster URL": "https://image.tmdb.org/t/p/w500/uE8f2c2tN20cWkX4zM53Gk3j1jV.jpg",
        "Popularity": 70.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Chhota Bheem: Kung Fu Dhamaka",
        "Genres": "Animation, Comedy, Adventure, Family, Fantasy",
        "Overview": "Chhota Bheem and his brave friends travel to China to participate in an prestigious martial arts tournament. When the princess of China is suddenly kidnapped by a demonic villain, Bheem uses his kung fu skills, wisdom, and teamwork to rescue her and save the kingdom from destruction.",
        "Language": "hi",
        "Release Year": 2019,
        "Vote Average": 7.2,
        "Poster URL": "https://image.tmdb.org/t/p/w500/mE8f2c2tN20cWkX4zM53Gk3j1jV.jpg",
        "Popularity": 75.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Kabir Singh",
        "Genres": "Drama, Romance",
        "Overview": "Kabir Singh is a brilliant but hot-tempered house surgeon who falls madly in love with a first-year student, Preeti. When her father rejects him and forces her to marry another man, Kabir goes down a self-destructive path of heavy alcohol and drug abuse, struggling to cope with his heartbreak.",
        "Language": "hi",
        "Release Year": 2019,
        "Vote Average": 7.1,
        "Poster URL": "https://image.tmdb.org/t/p/w500/w7gTA3Wn0Y5bT0x6t0QhJtH0aL.jpg",
        "Popularity": 80.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Gangs of Wasseypur",
        "Genres": "Action, Crime, Drama, Thriller",
        "Overview": "An epic, multi-generational crime saga centered on the coal mafia of Wasseypur, India. It details the fierce, decades-long blood feud between Sardar Khan, his sons, and the ruthless politician-gangster Ramadhir Singh, filled with explosive violence, local politics, and power struggles.",
        "Language": "hi",
        "Release Year": 2012,
        "Vote Average": 8.2,
        "Poster URL": "https://image.tmdb.org/t/p/w500/A31c2tN20cWkX4zM53Gk3j1jV.jpg",
        "Popularity": 85.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Andhadhun",
        "Genres": "Comedy, Crime, Thriller, Mystery",
        "Overview": "Akash is a blind pianist who accidentally witnesses the murder of a former film star at his apartment. As Akash gets caught in a web of deceit, betrayal, and suspicious police investigations, it becomes clear that there is far more to his blindness than meets the eye.",
        "Language": "hi",
        "Release Year": 2018,
        "Vote Average": 8.2,
        "Poster URL": "https://image.tmdb.org/t/p/w500/dyowC17242Zw96gEkzX0zG5YLOoa7.jpg",
        "Popularity": 89.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Zindagi Na Milegi Dobara",
        "Genres": "Comedy, Drama, Romance",
        "Overview": "Three childhood friends—Kabir, Imran, and Arjun—reunite for a three-week bachelor road trip in Spain. During their journey, they participate in extreme adventure sports like skydiving and deep-sea diving, confronting their deepest fears, healing past wounds, and rediscovering life and love.",
        "Language": "hi",
        "Release Year": 2011,
        "Vote Average": 8.1,
        "Poster URL": "https://image.tmdb.org/t/p/w500/b8f2c2tN20cWkX4zM53Gk3j1jV.jpg",
        "Popularity": 91.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "PK",
        "Genres": "Comedy, Drama, Science Fiction",
        "Overview": "An innocent humanoid alien lands on Earth in Rajasthan, India, but immediately loses the remote control to his spaceship. Confused by human behavior, religion, and customs, he asks innocent questions that expose the hypocrisy, blind beliefs, and dogmas of religious leaders, while falling in love with a journalist.",
        "Language": "hi",
        "Release Year": 2014,
        "Vote Average": 8.1,
        "Poster URL": "https://image.tmdb.org/t/p/w500/z6P2kosZw96gEkzX0zG5YLOoa7.jpg",
        "Popularity": 93.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Dilwale Dulhania Le Jayenge",
        "Genres": "Drama, Romance, Comedy",
        "Overview": "Raj and Simran are young non-resident Indians living in London who fall in love during a scenic train journey through Europe. When Raj learns Simran's conservative father has arranged her marriage in India, he travels to Punjab to win over her entire family and receive her father's blessing.",
        "Language": "hi",
        "Release Year": 1995,
        "Vote Average": 8.2,
        "Poster URL": "https://image.tmdb.org/t/p/w500/27P2kosZw96gEkzX0zG5YLOoa7.jpg",
        "Popularity": 94.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Chak De! India",
        "Genres": "Drama, Family",
        "Overview": "Kabir Khan, a disgraced former captain of the Indian men's national field hockey team, seeks redemption by coaching the struggling Indian women's national hockey team. He must overcome chauvinism, regional rivalries, and internal politics to unite the team and lead them to a world championship victory.",
        "Language": "hi",
        "Release Year": 2007,
        "Vote Average": 8.1,
        "Poster URL": "https://image.tmdb.org/t/p/w500/y8f2c2tN20cWkX4zM53Gk3j1jV.jpg",
        "Popularity": 82.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Queen",
        "Genres": "Comedy, Drama",
        "Overview": "Rani is a shy, simple girl from Delhi whose fiancé calls off their wedding just days before the ceremony. Devastated but determined, Rani decides to go on their pre-booked honeymoon to Paris and Amsterdam all by herself, discovering independence, lifelong friends, and self-confidence along the way.",
        "Language": "hi",
        "Release Year": 2013,
        "Vote Average": 8.1,
        "Poster URL": "https://image.tmdb.org/t/p/w500/x8f2c2tN20cWkX4zM53Gk3j1jV.jpg",
        "Popularity": 80.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Krrish",
        "Genres": "Action, Science Fiction, Adventure",
        "Overview": "Krishna inherits supernatural powers from his father, Rohit, who was contacted by an alien. Living a secluded life in the mountains, Krishna falls in love with a visiting girl, Priya, and follows her to Singapore, where he takes on the secret superhero identity of Krrish to stop a mad scientist.",
        "Language": "hi",
        "Release Year": 2006,
        "Vote Average": 6.4,
        "Poster URL": "https://image.tmdb.org/t/p/w500/v8f2c2tN20cWkX4zM53Gk3j1jV.jpg",
        "Popularity": 75.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Koi... Mil Gaya",
        "Genres": "Science Fiction, Drama, Family",
        "Overview": "Rohit is a developmentally disabled young man who accidentally contacts alien life using his late father's computer equipment. A friendly blue extraterrestrial, Jadoo, is left behind on Earth and uses his cosmic powers to cure Rohit's mental disability and grant him superhuman strength and intelligence.",
        "Language": "hi",
        "Release Year": 2003,
        "Vote Average": 7.1,
        "Poster URL": "https://image.tmdb.org/t/p/w500/u8f2c2tN20cWkX4zM53Gk3j1jV.jpg",
        "Popularity": 78.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Drishyam",
        "Genres": "Crime, Thriller, Drama, Mystery",
        "Overview": "Vijay Salgaonkar is a local cable operator and film fanatic who lives happily with his wife and daughters. When his family accidentally kills the son of a high-ranking, ruthless police officer in self-defense, Vijay uses his knowledge of crime cinema to construct a flawless alibi and protect his family.",
        "Language": "hi",
        "Release Year": 2015,
        "Vote Average": 8.2,
        "Poster URL": "https://image.tmdb.org/t/p/w500/t8f2c2tN20cWkX4zM53Gk3j1jV.jpg",
        "Popularity": 87.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Uri: The Surgical Strike",
        "Genres": "Action, War, History",
        "Overview": "Based on true events, Major Vihaan Singh Shergill of the Indian Army leads a covert, high-precision surgical strike operation against terrorist launchpads across the border in Pakistan, avenging the deadly attack on an army base in Uri that killed his fellow soldiers.",
        "Language": "hi",
        "Release Year": 2019,
        "Vote Average": 8.2,
        "Poster URL": "https://image.tmdb.org/t/p/w500/s8f2c2tN20cWkX4zM53Gk3j1jV.jpg",
        "Popularity": 86.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Hera Pheri",
        "Genres": "Comedy",
        "Overview": "Three eccentric roommates—a kind-hearted landlord, Baburao, and two desperate tenants, Raju and Shyam—are struggling to make ends meet. Their lives take a hilarious, chaotic turn when they receive a wrong telephone call from a kidnapper demanding ransom, and decide to intercept the money.",
        "Language": "hi",
        "Release Year": 2000,
        "Vote Average": 8.2,
        "Poster URL": "https://image.tmdb.org/t/p/w500/r8f2c2tN20cWkX4zM53Gk3j1jV.jpg",
        "Popularity": 88.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "My Name Is Khan",
        "Genres": "Drama, Romance",
        "Overview": "Rizwan Khan, an honorable Muslim man with Asperger's syndrome, falls in love with and marries Mandira, a Hindu single mother in San Francisco. After the tragic September 11 attacks, their family faces prejudice and tragedy, prompting Rizwan to cross the United States on a journey to meet the President and clear his name.",
        "Language": "hi",
        "Release Year": 2010,
        "Vote Average": 7.9,
        "Poster URL": "https://image.tmdb.org/t/p/w500/q8f2c2tN20cWkX4zM53Gk3j1jV.jpg",
        "Popularity": 84.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Swades",
        "Genres": "Drama",
        "Overview": "Mohan Bhargava, a successful project manager at NASA in the United States, travels back to India to find his childhood nanny. Staying in a remote, underdeveloped village, he witnesses the hardships of rural life and decides to use his engineering knowledge to build a local micro-hydroelectric power plant, transforming the village.",
        "Language": "hi",
        "Release Year": 2004,
        "Vote Average": 8.2,
        "Poster URL": "https://image.tmdb.org/t/p/w500/p8f2c2tN20cWkX4zM53Gk3j1jV.jpg",
        "Popularity": 81.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Yeh Jawaani Hai Deewani",
        "Genres": "Comedy, Drama, Romance",
        "Overview": "Kabir (Bunny) and Naina meet during a trekking trip in Manali. Bunny is a free spirit who dreams of traveling the world, while Naina is a studious girl. Years later, they reunite at a friend's wedding in Udaipur, finding themselves torn between career ambitions, personal dreams, and their growing love.",
        "Language": "hi",
        "Release Year": 2013,
        "Vote Average": 7.2,
        "Poster URL": "https://image.tmdb.org/t/p/w500/o8f2c2tN20cWkX4zM53Gk3j1jV.jpg",
        "Popularity": 87.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Barfi!",
        "Genres": "Comedy, Drama, Romance",
        "Overview": "Set in the 1970s in Darjeeling, Barfi is a charming deaf-mute young man who forms a unique, deep relationship with Shruti. However, societal pressure forces Shruti to marry another. Years later, Barfi's path crosses with Jhilmil, an autistic girl, leading to a heartwarming and emotional story of love.",
        "Language": "hi",
        "Release Year": 2012,
        "Vote Average": 8.1,
        "Poster URL": "https://image.tmdb.org/t/p/w500/n8f2c2tN20cWkX4zM53Gk3j1jV.jpg",
        "Popularity": 83.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    {
        "Movie Title": "Munna Bhai M.B.B.S.",
        "Genres": "Comedy, Drama",
        "Overview": "Munna is a good-natured Mumbai gangster who pretends to be a successful doctor to please his honest father. When his lie is exposed and his father is humiliated, Munna vows to get a real medical degree, enrolling in a top college where he cures patients with humor, compassion, and hugs.",
        "Language": "hi",
        "Release Year": 2003,
        "Vote Average": 8.1,
        "Poster URL": "https://image.tmdb.org/t/p/w500/m8f2c2tN20cWkX4zM53Gk3j1jV.jpg",
        "Popularity": 85.0,
        "Adult Flag": 0,
        "Original Language": "hi"
    },
    
    # --- TAMIL (Kollywood) ---
    {
        "Movie Title": "Vikram",
        "Genres": "Action, Thriller, Crime",
        "Overview": "A high-octane action thriller where a special ops team, led by a ruthless commander, is assigned to investigate a series of brutal mask-wearing murders. As the investigation deepens, they uncover a massive drug cartel run by a ruthless syndicate and cross paths with a mysterious vigilante.",
        "Language": "ta",
        "Release Year": 2022,
        "Vote Average": 8.3,
        "Poster URL": "https://image.tmdb.org/t/p/w500/t056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 94.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Kaithi",
        "Genres": "Action, Thriller, Crime",
        "Overview": "A recently released prisoner, Dilli, wants to meet his young daughter for the first time. However, his plans are interrupted when a sincere police officer recruits him to drive a massive truck full of unconscious, poisoned police officers to the hospital while escaping a gang chasing them.",
        "Language": "ta",
        "Release Year": 2019,
        "Vote Average": 8.5,
        "Poster URL": "https://image.tmdb.org/t/p/w500/l056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 90.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Jai Bhim",
        "Genres": "Drama, Crime, Mystery",
        "Overview": "A courageous, human-rights activist lawyer, Chandru, fights a legal battle in court for a poor tribal woman whose husband has gone missing from police custody after being falsely accused of theft. The case exposes the deep-rooted corruption, caste bias, and brutality within the police force.",
        "Language": "ta",
        "Release Year": 2021,
        "Vote Average": 8.9,
        "Poster URL": "https://image.tmdb.org/t/p/w500/k056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 96.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Soorarai Pottru",
        "Genres": "Drama",
        "Overview": "Inspired by true events, Nedumaaran Rajangam (Maara), a former air force captain from a remote village, dreams of launching a low-cost, budget airline for common people. He must fight against corrupt airline corporate giants, heavy bureaucratic red tape, and personal financial struggles to achieve his vision.",
        "Language": "ta",
        "Release Year": 2020,
        "Vote Average": 8.7,
        "Poster URL": "https://image.tmdb.org/t/p/w500/j056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 92.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Asuran",
        "Genres": "Action, Drama, Thriller",
        "Overview": "Sivasamy is a quiet, peace-loving farmer who lives with his family in a rural village. When his hot-headed elder son kills a wealthy, oppressive landlord to avenge their family's humiliation, Sivasamy must flee with his young son into the forests, using his hidden, violent past to protect them.",
        "Language": "ta",
        "Release Year": 2019,
        "Vote Average": 8.5,
        "Poster URL": "https://image.tmdb.org/t/p/w500/i056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 87.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "96",
        "Genres": "Drama, Romance",
        "Overview": "Ram and Janu are high school sweethearts who reunite after 22 years at a school reunion. Ram is a professional travel photographer who never married, while Janu is married and lives in Singapore. Over the course of a single emotional night, they reminisce about their youth and address unresolved feelings.",
        "Language": "ta",
        "Release Year": 2018,
        "Vote Average": 8.5,
        "Poster URL": "https://image.tmdb.org/t/p/w500/h056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 88.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Enthiran",
        "Genres": "Action, Science Fiction",
        "Overview": "A brilliant scientist, Dr. Vaseegaran, invents an advanced humanoid robot named Chitti to serve in the military. However, Chitti is upgraded to feel human emotions, falling in love with Vaseegaran's fiancée, Sana. Chitti is soon manipulated by a rival scientist into a destructive engine of war.",
        "Language": "ta",
        "Release Year": 2010,
        "Vote Average": 7.1,
        "Poster URL": "https://image.tmdb.org/t/p/w500/g056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 80.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Sivaji: The Boss",
        "Genres": "Action, Comedy, Drama",
        "Overview": "Sivaji is a wealthy software engineer who returns to India from the US with dreams of building free hospitals and colleges for the poor. Corrupt politicians and local businessmen strip him of his wealth, prompting him to use his street smarts, black money, and power to build his empire and execute justice.",
        "Language": "ta",
        "Release Year": 2007,
        "Vote Average": 7.5,
        "Poster URL": "https://image.tmdb.org/t/p/w500/f056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 83.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Baahubali: The Beginning",
        "Genres": "Action, Fantasy, Adventure",
        "Overview": "In the ancient kingdom of Mahishmati, a young, powerful man named Shivudu falls in love with a warrior girl. During his quest to win her heart, he climbs a massive waterfall and discovers his true royal heritage as the son of the legendary king Amarendra Baahubali, embarking on a quest for justice.",
        "Language": "ta",
        "Release Year": 2015,
        "Vote Average": 8.0,
        "Poster URL": "https://image.tmdb.org/t/p/w500/e056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 95.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Baahubali 2: The Conclusion",
        "Genres": "Action, Fantasy, Adventure",
        "Overview": "The epic continuation of the saga of Mahishmati. Shiva (Mahendra Baahubali) learns from his uncle Kattappa about the tragic betrayal and murder of his noble father, Amarendra Baahubali, by the power-hungry Bhallaladeva. Shiva raises an army to overthrow the tyrant and reclaim his rightful throne.",
        "Language": "ta",
        "Release Year": 2017,
        "Vote Average": 8.2,
        "Poster URL": "https://image.tmdb.org/t/p/w500/d056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 97.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Thuppakki",
        "Genres": "Action, Thriller, Crime",
        "Overview": "Jagadish, a Captain in the Indian Army and a covert intelligence agent, returns to Mumbai on vacation. While scouting, he stumbles upon a massive terrorist plot involving multiple sleeper cells planning bomb blasts in the city, leading to a high-stakes cat-and-mouse game to neutralize the cells.",
        "Language": "ta",
        "Release Year": 2012,
        "Vote Average": 8.1,
        "Poster URL": "https://image.tmdb.org/t/p/w500/c056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 84.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Kaththi",
        "Genres": "Action, Drama, Thriller",
        "Overview": "Kathiresan, an escaped criminal and mastermind, switches places with his lookalike Jeevanandham, a quiet social activist fighting for farmers' land rights against a greedy corporate company. When Kathiresan realizes Jeeva's noble cause, he takes on the corporate empire himself to save the village.",
        "Language": "ta",
        "Release Year": 2014,
        "Vote Average": 8.0,
        "Poster URL": "https://image.tmdb.org/t/p/w500/b056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 82.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Mersal",
        "Genres": "Action, Thriller, Drama",
        "Overview": "A magician, Vetri, and a doctor, Maaran, are identical twins separated at birth who unite to avenge the death of their parents. They target corrupt medical practitioners and medical mafias who are charging exorbitant fees for basic treatments, exposing the corruption in the healthcare industry.",
        "Language": "ta",
        "Release Year": 2017,
        "Vote Average": 7.6,
        "Poster URL": "https://image.tmdb.org/t/p/w500/a056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 81.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Sarkar",
        "Genres": "Action, Drama",
        "Overview": "Sundar Ramaswamy, a highly successful NRI corporate giant, returns to Chennai to cast his vote in the local assembly elections, only to discover that someone else has already cast his vote illegally. Incensed, Sundar decides to fight a legal and political battle, eventually entering the elections.",
        "Language": "ta",
        "Release Year": 2018,
        "Vote Average": 7.0,
        "Poster URL": "https://image.tmdb.org/t/p/w500/z056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 79.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Petta",
        "Genres": "Action, Drama, Thriller",
        "Overview": "Kaali is a charismatic, friendly hostel warden who takes a job at a college in Ooty. He soon gets involved with local student gangs, sorting out their issues. However, it is revealed that Kaali has a violent past, and he has taken this job to seek revenge on an old politician-gangster enemy.",
        "Language": "ta",
        "Release Year": 2019,
        "Vote Average": 7.3,
        "Poster URL": "https://image.tmdb.org/t/p/w500/y056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 80.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Anniyan",
        "Genres": "Action, Thriller, Drama",
        "Overview": "Ramanujam is an honest lawyer who suffers from multiple personality disorder due to frustration with the corruption and indifference in society. He creates two other personalities: Remo, a stylish fashion model, and Anniyan, a ruthless vigilante who executes corrupt individuals based on ancient punishments.",
        "Language": "ta",
        "Release Year": 2005,
        "Vote Average": 8.2,
        "Poster URL": "https://image.tmdb.org/t/p/w500/x056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 85.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Ghilli",
        "Genres": "Action, Comedy, Romance",
        "Overview": "Velu is a state-level kabaddi player who travels to Madurai for a tournament. During his trip, he rescues Dhanalakshmi from a powerful, ruthless politician who is forcing her to marry him. Velu hides Dhanalakshmi in his own house in Chennai, leading to a thrilling chase and fight to protect her.",
        "Language": "ta",
        "Release Year": 2004,
        "Vote Average": 8.0,
        "Poster URL": "https://image.tmdb.org/t/p/w500/w056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 83.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Vada Chennai",
        "Genres": "Action, Crime, Drama, Thriller",
        "Overview": "An epic, gritty gangster film set in North Chennai. Anbu, a talented carrom player, is reluctantly drawn into a local turf war between rival gang leaders who are vying for control of the region, eventually rising to become a powerful defender of his community.",
        "Language": "ta",
        "Release Year": 2018,
        "Vote Average": 8.5,
        "Poster URL": "https://image.tmdb.org/t/p/w500/v056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 86.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Master",
        "Genres": "Action, Drama, Thriller",
        "Overview": "JD is an alcoholic, unconventional professor who is sent to a juvenile correction home for a three-month assignment. There, he clashes with Bhavani, a ruthless gangster who uses the young inmates of the home to carry out his illegal activities and take the blame for his crimes.",
        "Language": "ta",
        "Release Year": 2021,
        "Vote Average": 7.8,
        "Poster URL": "https://image.tmdb.org/t/p/w500/u056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 88.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },
    {
        "Movie Title": "Super Deluxe",
        "Genres": "Comedy, Drama, Thriller",
        "Overview": "An anthology film depicting four stories of individuals in Chennai who are placed in extraordinary, unexpected circumstances. A transgender woman reunites with her son, a young wife tries to dispose of her lover's corpse, and a group of teenage boys discover a dark secret.",
        "Language": "ta",
        "Release Year": 2019,
        "Vote Average": 8.3,
        "Poster URL": "https://image.tmdb.org/t/p/w500/s056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 84.0,
        "Adult Flag": 0,
        "Original Language": "ta"
    },

    # --- TELUGU (Tollywood) ---
    {
        "Movie Title": "RRR",
        "Genres": "Action, Drama, History",
        "Overview": "A highly fictionalized story of two legendary Indian revolutionaries, Alluri Sitarama Raju and Komaram Bheem, who strike up a deep, unexpected friendship during the 1920s British colonial rule in India, joining forces to launch an epic rebellion against their oppressors.",
        "Language": "te",
        "Release Year": 2022,
        "Vote Average": 8.2,
        "Poster URL": "https://image.tmdb.org/t/p/w500/nEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 98.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Pushpa: The Rise",
        "Genres": "Action, Crime, Drama, Thriller",
        "Overview": "Pushpa Raj is a coolie who rises rapidly in the dangerous world of red sandalwood smuggling in the forests of Seshachalam. With his sharp mind and fearless attitude, he climbs to the top of the syndicate, clashing with rival smugglers and a ruthless, egotistical police officer.",
        "Language": "te",
        "Release Year": 2021,
        "Vote Average": 7.6,
        "Poster URL": "https://image.tmdb.org/t/p/w500/xEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 92.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Baahubali: The Beginning",
        "Genres": "Action, Fantasy, Adventure",
        "Overview": "In the ancient kingdom of Mahishmati, a young, powerful man named Shivudu falls in love with a warrior girl. During his quest to win her heart, he climbs a massive waterfall and discovers his true royal heritage as the son of the legendary king Amarendra Baahubali, embarking on a quest for justice.",
        "Language": "te",
        "Release Year": 2015,
        "Vote Average": 8.0,
        "Poster URL": "https://image.tmdb.org/t/p/w500/e056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 95.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Baahubali 2: The Conclusion",
        "Genres": "Action, Fantasy, Adventure",
        "Overview": "The epic continuation of the saga of Mahishmati. Shiva (Mahendra Baahubali) learns from his uncle Kattappa about the tragic betrayal and murder of his noble father, Amarendra Baahubali, by the power-hungry Bhallaladeva. Shiva raises an army to overthrow the tyrant and reclaim his rightful throne.",
        "Language": "te",
        "Release Year": 2017,
        "Vote Average": 8.2,
        "Poster URL": "https://image.tmdb.org/t/p/w500/d056ZpT5r78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 97.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Arjun Reddy",
        "Genres": "Drama, Romance",
        "Overview": "Arjun Reddy is a brilliant but short-tempered medical student who falls deeply in love with a junior student, Preeti. When her father rejects him and marries her off, Arjun goes down a self-destructive path of heavy alcohol and drug abuse, struggling to cope with his heartbreak.",
        "Language": "te",
        "Release Year": 2017,
        "Vote Average": 8.1,
        "Poster URL": "https://image.tmdb.org/t/p/w500/wEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 88.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Mahanati",
        "Genres": "Drama, History",
        "Overview": "A biographical film documenting the tragic life, career, and rise of the legendary south Indian actress Savitri. Savitri, who dominated the film industry for decades, falls into depression, alcoholism, and financial ruin due to complex personal relationships and betrayals.",
        "Language": "te",
        "Release Year": 2018,
        "Vote Average": 8.5,
        "Poster URL": "https://image.tmdb.org/t/p/w500/vEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 84.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Jersey",
        "Genres": "Drama, Family",
        "Overview": "Arjun is a highly talented but failed 36-year-old cricketer who quit the sport years ago. He decides to rejoin the Ranji trophy team to fulfill his young son's dream of getting a team jersey, facing heavy physical strain and societal doubts to prove his worth.",
        "Language": "te",
        "Release Year": 2019,
        "Vote Average": 8.6,
        "Poster URL": "https://image.tmdb.org/t/p/w500/uEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 85.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Geetha Govindam",
        "Genres": "Romance, Comedy",
        "Overview": "Vijay Govind is an innocent college lecturer who dreams of marrying a traditional girl. He meets Geetha on a bus journey and accidentally commits a mistake, earning her anger. He must work hard to clear his name and win her heart when she turns out to be his sister's friend.",
        "Language": "te",
        "Release Year": 2018,
        "Vote Average": 7.7,
        "Poster URL": "https://image.tmdb.org/t/p/w500/tEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 83.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Ala Vaikunthapurramuloo",
        "Genres": "Action, Comedy, Drama",
        "Overview": "Bantu is a middle-class young man whose father, Valmiki, treats him with indifference. Bantu later learns that Valmiki switched him at birth with a wealthy businessman's son to give his own son a luxurious life. Bantu enters the mansion of his real parents to protect them from danger.",
        "Language": "te",
        "Release Year": 2020,
        "Vote Average": 7.3,
        "Poster URL": "https://image.tmdb.org/t/p/w500/sEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 89.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Rangasthalam",
        "Genres": "Action, Drama, Thriller",
        "Overview": "Chitti Babu is a partially deaf, simple villager who operates a water boat for irrigation. When his foreign-educated brother, Kumar Babu, decides to run in the local elections against the corrupt, cruel village president who has ruled for 30 years, Chitti Babu must protect his brother from danger.",
        "Language": "te",
        "Release Year": 2018,
        "Vote Average": 8.4,
        "Poster URL": "https://image.tmdb.org/t/p/w500/rEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 87.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Eega",
        "Genres": "Fantasy, Action, Comedy",
        "Overview": "Nani is a young man who is brutally murdered by a greedy businessman, Sudeep, who desires Nani's love interest, Bindu. Nani is reborn as a common housefly and uses his tiny size, speed, and intelligence to torment Sudeep and protect Bindu from his advances.",
        "Language": "te",
        "Release Year": 2012,
        "Vote Average": 7.7,
        "Poster URL": "https://image.tmdb.org/t/p/w500/qEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 85.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Magadheera",
        "Genres": "Fantasy, Action, Romance",
        "Overview": "A historical fantasy film where Harsha, a modern-day bike stuntman, accidentally touches a girl's hand and remembers his past life from 400 years ago. In his past life, he was Kala Bhairava, a legendary royal warrior of Rajasthan who fell in love with Princess Mithravinda and died protecting her.",
        "Language": "te",
        "Release Year": 2009,
        "Vote Average": 7.7,
        "Poster URL": "https://image.tmdb.org/t/p/w500/pEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 83.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Pokiri",
        "Genres": "Action, Crime, Thriller",
        "Overview": "Pandu is a cold-blooded, ruthless hitman who works for local mafia syndicates for money. During his missions, he falls in love with an innocent girl, Shruti. However, a major twist reveals that Pandu is actually an undercover police officer, Krishna Manohar, on a mission to eliminate the gang.",
        "Language": "te",
        "Release Year": 2006,
        "Vote Average": 8.0,
        "Poster URL": "https://image.tmdb.org/t/p/w500/oEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 81.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Athadu",
        "Genres": "Action, Thriller, Drama",
        "Overview": "Nandu is a highly professional, cold assassin who is framed for a murder he did not commit. While fleeing the police, he switches places with a quiet villager, Pardhu, who was accidentally killed. Nandu enters Pardhu's large ancestral family home, learning about family love and fighting to clear his name.",
        "Language": "te",
        "Release Year": 2005,
        "Vote Average": 8.2,
        "Poster URL": "https://image.tmdb.org/t/p/w500/nEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 82.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Gabbar Singh",
        "Genres": "Action, Comedy, Drama",
        "Overview": "Gabbar Singh is a rebellious, charismatic police officer who adopts the name of the famous Sholay villain. Sent to a crime-ridden village, he clashes with Siddhappa Naidu, a corrupt local politician-gangster, using his unorthodox, humorous, and violent methods to restore peace.",
        "Language": "te",
        "Release Year": 2012,
        "Vote Average": 7.1,
        "Poster URL": "https://image.tmdb.org/t/p/w500/mEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 79.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Kartikeya 2",
        "Genres": "Adventure, Mystery, Thriller, Fantasy",
        "Overview": "Dr. Kartikeya is a rational, scientific doctor who travels to Dwarka, where he gets dragged into a ancient mystery. He must decode a series of historical clues left behind by Lord Krishna to find a powerful, mythical anklet before a cult retrieves it to gain power.",
        "Language": "te",
        "Release Year": 2022,
        "Vote Average": 7.4,
        "Poster URL": "https://image.tmdb.org/t/p/w500/lEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 80.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Sita Ramam",
        "Genres": "Drama, Romance",
        "Overview": "Lieutenant Ram is an orphaned army officer serving at the Kashmir border. He receives a series of beautiful, anonymous love letters from a girl named Sita Mahalakshmi. He sets out on a journey to find her, uncovering a heartwarming, tragic story of love, duty, and sacrifice across national borders.",
        "Language": "te",
        "Release Year": 2022,
        "Vote Average": 8.6,
        "Poster URL": "https://image.tmdb.org/t/p/w500/kEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 91.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Srimanthudu",
        "Genres": "Action, Drama, Family",
        "Overview": "Harsha is the wealthy heir of a multi-billion dollar business empire. Feeling empty, he refuses his father's business and decides to adopt an underdeveloped village, Devarakonda, which is his ancestral birthplace. He fights local goons, develops schools, and builds water infrastructure.",
        "Language": "te",
        "Release Year": 2015,
        "Vote Average": 7.5,
        "Poster URL": "https://image.tmdb.org/t/p/w500/jEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 80.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Julayi",
        "Genres": "Action, Comedy, Crime, Thriller",
        "Overview": "Ravindra Narayan is a highly intelligent, street-smart slacker who believes in easy money. He crosses paths with Bittu, a cold-blooded bank robber. Ravindra helps the police foil Bittu's 150-crore heist, sparking a fierce, intellectual battle of wits and survival between the two.",
        "Language": "te",
        "Release Year": 2012,
        "Vote Average": 7.7,
        "Poster URL": "https://image.tmdb.org/t/p/w500/iEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 82.0,
        "Adult Flag": 0,
        "Original Language": "te"
    },
    {
        "Movie Title": "Janatha Garage",
        "Genres": "Action, Drama",
        "Overview": "Anand is an environmental activist student who travels to Hyderabad. There, he meets Sathyam, a respected local leader who runs an automobile workshop called Janatha Garage, which serves as a vigilante court of justice for the oppressed. Anand joins Sathyam's crusade to protect the environment and people.",
        "Language": "te",
        "Release Year": 2016,
        "Vote Average": 7.3,
        "Poster URL": "https://image.tmdb.org/t/p/w500/hEu41065p9T78X20z93W5nQhJtH0aL.jpg",
        "Popularity": 81.0,
        "Adult Flag": 0,
        "Original Language": "te"
    }
]

def preprocess():
    print("Starting preprocessing...")
    
    # 1. Connect to database
    db_path = 'movies.db'
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found at {db_path}")
        
    print(f"Loading data from {db_path}...")
    conn = sqlite3.connect(db_path)
    
    # Fetch English movies only, as other languages are not supported
    # Select columns we need
    query = """
    SELECT title, genres, overview, language, release_year, vote_average, popularity, poster_path, tmdb_id, runtime, director, "cast", backdrop_path
    FROM movies
    WHERE language = 'en';
    """
    db_df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"Extracted {len(db_df)} English movies from database.")
    
    # 2. Process English movies
    processed_db_movies = []
    for idx, row in db_df.iterrows():
        title_clean = clean_title(row['title'])
        genres_clean = map_genres(row['genres'])
        
        # Construct Poster URL from poster_path
        poster_url = ""
        if row['poster_path'] and str(row['poster_path']).strip():
            poster_url = f"https://image.tmdb.org/t/p/w500{row['poster_path'].strip()}"
            
        # Construct Backdrop URL from backdrop_path
        backdrop_url = ""
        if row['backdrop_path'] and str(row['backdrop_path']).strip():
            backdrop_url = f"https://image.tmdb.org/t/p/w1280{row['backdrop_path'].strip()}"
            
        # Scale rating from 0-5 to 0-10
        vote_avg = row['vote_average']
        if pd.notna(vote_avg):
            vote_avg = round(float(vote_avg) * 2, 2)
        else:
            vote_avg = 5.0  # Fallback median rating
            
        popularity = row['popularity']
        if pd.isna(popularity):
            popularity = 10.0  # Fallback popularity
            
        release_year = row['release_year']
        if pd.isna(release_year):
            release_year = 2000
            
        overview = row['overview'] if row['overview'] else ""
        
        runtime = row['runtime']
        if pd.isna(runtime) or int(runtime) <= 0:
            runtime = 120
        else:
            runtime = int(runtime)
            
        director = row['director'] if row['director'] and str(row['director']).strip() else "Unknown Director"
        cast = row['cast'] if row['cast'] and str(row['cast']).strip() else "Unknown Cast"
        
        processed_db_movies.append({
            "Movie Title": title_clean,
            "Genres": genres_clean,
            "Overview": overview,
            "Language": "en",
            "Release Year": int(release_year),
            "Vote Average": float(vote_avg),
            "Poster URL": poster_url,
            "Popularity": float(popularity),
            "Adult Flag": 0,  # Default English movies as non-adult
            "Original Language": "en",
            "Runtime": runtime,
            "Director": director,
            "Cast": cast,
            "Backdrop URL": backdrop_url
        })
        
    df_en = pd.DataFrame(processed_db_movies)
    
    # 3. Create DataFrame for Indian movies and inject metadata defaults/overrides
    df_in = pd.DataFrame(INDIAN_MOVIES)
    df_in['Runtime'] = 140
    df_in['Director'] = 'Various Directors'
    df_in['Cast'] = 'Various Cast'
    df_in['Backdrop URL'] = ''
    
    title_overrides = {
        "3 Idiots": {"Runtime": 170, "Director": "Rajkumar Hirani", "Cast": "Aamir Khan, Kareena Kapoor, R. Madhavan"},
        "Dangal": {"Runtime": 161, "Director": "Nitesh Tiwari", "Cast": "Aamir Khan, Sakshi Tanwar, Fatima Sana Shaikh"},
        "RRR": {"Runtime": 187, "Director": "S.S. Rajamouli", "Cast": "N.T. Rama Rao Jr., Ram Charan, Alia Bhatt"},
        "Baahubali: The Beginning": {"Runtime": 159, "Director": "S.S. Rajamouli", "Cast": "Prabhas, Rana Daggubati, Anushka Shetty"},
        "Baahubali 2: The Conclusion": {"Runtime": 167, "Director": "S.S. Rajamouli", "Cast": "Prabhas, Rana Daggubati, Anushka Shetty"},
        "Sholay": {"Runtime": 204, "Director": "Ramesh Sippy", "Cast": "Amitabh Bachchan, Dharmendra, Hema Malini"},
        "Dilwale Dulhania Le Jayenge": {"Runtime": 189, "Director": "Aditya Chopra", "Cast": "Shah Rukh Khan, Kajol, Amrish Puri"},
        "Lagaan": {"Runtime": 224, "Director": "Ashutosh Gowariker", "Cast": "Aamir Khan, Gracy Singh, Rachel Shelley"},
        "Gangs of Wasseypur": {"Runtime": 321, "Director": "Anurag Kashyap", "Cast": "Manoj Bajpayee, Nawazuddin Siddiqui, Richa Chadda"},
        "K.G.F: Chapter 1": {"Runtime": 156, "Director": "Prashanth Neel", "Cast": "Yash, Srinidhi Shetty, Ramachandra Raju"},
        "K.G.F: Chapter 2": {"Runtime": 168, "Director": "Prashanth Neel", "Cast": "Yash, Sanjay Dutt, Raveena Tandon"},
        "Kantara": {"Runtime": 150, "Director": "Rishab Shetty", "Cast": "Rishab Shetty, Sapthami Gowda, Kishore"},
        "Pushpa: The Rise": {"Runtime": 179, "Director": "Sukumar", "Cast": "Allu Arjun, Rashmika Mandanna, Fahadh Faasil"}
    }
    
    for title, overrides in title_overrides.items():
        mask = df_in['Movie Title'].str.lower() == title.lower()
        if mask.any():
            for key, val in overrides.items():
                df_in.loc[mask, key] = val
    
    # 4. Merge datasets
    df_combined = pd.concat([df_en, df_in], ignore_index=True)
    
    # Deduplicate by title, release year, and language
    df_combined.drop_duplicates(subset=["Movie Title", "Release Year", "Language"], keep="first", inplace=True)
    
    # Handle missing overviews or values
    df_combined["Overview"] = df_combined["Overview"].fillna("").astype(str)
    df_combined["Genres"] = df_combined["Genres"].fillna("Drama").astype(str)
    
    # Standardize values
    df_combined["Release Year"] = df_combined["Release Year"].fillna(2000).astype(int)
    df_combined["Vote Average"] = df_combined["Vote Average"].fillna(5.0).astype(float)
    df_combined["Popularity"] = df_combined["Popularity"].fillna(10.0).astype(float)
    df_combined["Adult Flag"] = df_combined["Adult Flag"].fillna(0).astype(int)
    
    # Create directory if not exists
    os.makedirs('data', exist_ok=True)
    
    csv_path = 'data/movies.csv'
    df_combined.to_csv(csv_path, index=False)
    print(f"Saved {len(df_combined)} cleaned movies to {csv_path}")
    
    # 5. Fit and save TF-IDF vectorizer and matrix
    print("Fitting TF-IDF vectorizer on movie overviews...")
    
    # Fill empty overviews with title and genre to give at least some keywords
    corpus = []
    for idx, row in df_combined.iterrows():
        txt = row['Overview']
        if not txt.strip():
            # Fallback text so TF-IDF doesn't fail on empty strings
            txt = f"{row['Movie Title']}. A movie in the genre of {row['Genres']}."
        corpus.append(txt)
        
    vectorizer = TfidfVectorizer(stop_words='english', min_df=1, max_df=0.9, ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(corpus)
    
    vectorizer_path = 'data/tfidf_vectorizer.pkl'
    matrix_path = 'data/tfidf_matrix.pkl'
    
    joblib.dump(vectorizer, vectorizer_path)
    joblib.dump(tfidf_matrix, matrix_path)
    
    print(f"Saved TF-IDF models to data/ directory.")
    print("Preprocessing completed successfully!")

if __name__ == '__main__':
    preprocess()
