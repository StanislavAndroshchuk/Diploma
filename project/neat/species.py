# neat/species.py

import itertools
import random
import math

# Припускаємо, що клас Genome імпортується або доступний
from .genome import Genome # Якщо в тому ж пакеті

class Species:
    """
    Представляє вид (Species) в алгоритмі NEAT.
    Групує генетично схожі геноми для захисту інновацій
    та спільного використання пристосованості (fitness sharing).
    """
    _species_counter = itertools.count(1) # Почнемо ID видів з 1

    def __init__(self, first_genome: Genome):
        """
        Ініціалізує новий вид.

        Args:
            first_genome (Genome): Перший геном, який стає представником
                                    цього нового виду.
        """
        if not isinstance(first_genome, Genome):
            raise TypeError("first_genome must be an instance of Genome")

        self.id = next(Species._species_counter)
        # Представник використовується для порівняння при додаванні нових членів
        # Копіюємо, щоб зміни в оригінальному геномі не впливали на представника минулого покоління
        self.representative = first_genome.copy()
        self.members = [first_genome] # Список об'єктів Genome
        first_genome.species_id = self.id # Призначаємо ID виду геному

        # Атрибути для відстеження стану виду
        self.generations_since_improvement = 0 # Лічильник стагнації
        self.best_fitness_ever = first_genome.fitness # Найкращий фітнес, бачений у цьому виді
        self.total_adjusted_fitness = 0.0 # Сума скоригованих фітнесів членів (для розрахунку нащадків)
        self.offspring_count = 0 # Розрахована кількість нащадків для наступного покоління

    def add_member(self, genome: Genome):
        """Додає геном до списку членів цього виду."""
        if not isinstance(genome, Genome):
            raise TypeError("member must be an instance of Genome")
        self.members.append(genome)
        genome.species_id = self.id # Встановлюємо ID виду для геному

    def update_representative(self):
        """Оновлює представника виду, вибираючи випадкового члена."""
        if self.members:
            # У статті NEAT зазначено вибирати випадкового члена з ПОПЕРЕДНЬОГО покоління.
            # Оскільки ми оновлюємо *після* формування виду, вибираємо з поточних.
            # Якщо зберігати представників минулого покоління, логіка буде іншою.
            self.representative = random.choice(self.members)
        else:
            # Ця ситуація може виникнути, якщо вид стає порожнім перед оновленням
            self.representative = None
            # print(f"Warning: Species {self.id} has no members during representative update.")

    def sort_members_by_fitness(self):
        """Сортує членів виду за їхнім raw fitness (від кращого до гіршого)."""
        self.members.sort(key=lambda g: g.fitness, reverse=True)

    def update_stagnation_and_best_fitness(self):
        """
        Оновлює лічильник стагнації та найкращий фітнес виду.
        Викликається ПІСЛЯ сортування членів.
        """
        if not self.members:
            # Якщо вид порожній, він все одно стагнує (і, ймовірно, буде видалений)
            self.generations_since_improvement += 1
            return

        current_best_fitness = self.members[0].fitness # Найкращий у цьому поколінні

        if current_best_fitness > self.best_fitness_ever:
            self.best_fitness_ever = current_best_fitness
            self.generations_since_improvement = 0 # Скидаємо стагнацію
            # print(f"Species {self.id} improved. Best fitness: {self.best_fitness_ever:.4f}") # Debug
        else:
            self.generations_since_improvement += 1
            # print(f"Species {self.id} stagnated ({self.generations_since_improvement} gens). Best fitness: {self.best_fitness_ever:.4f}") # Debug

    def calculate_adjusted_fitness_and_sum(self):
        """
        Розраховує скоригований фітнес для кожного члена (fitness sharing)
        та обчислює їх суму для виду. Має викликатись ПЕРЕД визначенням
        кількості нащадків.
        """
        num_members = len(self.members)
        if num_members == 0:
            self.total_adjusted_fitness = 0.0
            return

        self.total_adjusted_fitness = 0.0
        for genome in self.members:
            # Формула явного fitness sharing
            genome.adjusted_fitness = genome.fitness / float(num_members)
            self.total_adjusted_fitness += genome.adjusted_fitness

    def clear_members(self):
        """
        Очищає список членів та скидає пов'язані суми.
        Викликається перед фазою видоутворення наступного покоління.
        Представник та історія стагнації/фітнесу зберігаються.
        """
        self.members = []
        self.total_adjusted_fitness = 0.0
        self.offspring_count = 0

    def get_state_data(self) -> dict:
        """Збирає дані для збереження стану виду."""
        return {
            'id': self.id,
            'representative_id': self.representative.id if self.representative else None,
            'member_ids': [member.id for member in self.members if member],
            'generations_since_improvement': self.generations_since_improvement,
            'best_fitness_ever': self.best_fitness_ever,
            'offspring_count': self.offspring_count # Додано для повноти
        }
    
    @classmethod
    def load_from_state_data(cls, data: dict, genomes_map: dict) -> 'Species':
        """Створює екземпляр Species зі збережених даних."""
        rep_genome = genomes_map.get(data['representative_id'])
        if not rep_genome and data['member_ids']: # Якщо немає представника, але є члени
            first_member_id = data['member_ids'][0]
            rep_genome = genomes_map.get(first_member_id)

        if not rep_genome:
            # Це критична помилка, якщо немає жодного геному для представника
            # Можливо, варто створити "пустий" вид або викликати виняток
            # Для простоти, повернемо None, але це треба обробити вище
            print(f"Warning: Could not find representative genome for species data: {data}")
            # Як тимчасове рішення, можна створити "пустий" вид, якщо це допустимо,
            # але краще забезпечити наявність геномів.
            # Якщо вид не може існувати без представника, це треба обробляти.
            # Наприклад, можна спробувати знайти будь-який геном з member_ids.
            if data['member_ids']:
                 for mid in data['member_ids']:
                     if mid in genomes_map:
                         rep_genome = genomes_map[mid]
                         break
            if not rep_genome:
                 raise ValueError(f"Cannot restore species {data.get('id', 'Unknown')} without a valid representative or member.")


        # Створюємо вид з копією представника, щоб уникнути зміни оригіналу
        species_obj = cls(rep_genome.copy())
        species_obj.id = data['id']
        species_obj.generations_since_improvement = data['generations_since_improvement']
        species_obj.best_fitness_ever = data['best_fitness_ever']
        species_obj.offspring_count = data.get('offspring_count', 0)

        # Очищаємо членів (бо конструктор додав представника) і додаємо з ID
        species_obj.members = []
        for member_id in data['member_ids']:
            if member_id in genomes_map:
                member_genome = genomes_map[member_id]
                species_obj.add_member(member_genome)
        
        # Важливо оновити представника на актуальний об'єкт з популяції
        if species_obj.members:
            # Спробуємо знайти оригінального представника серед членів
            found_rep_in_members = next((m for m in species_obj.members if m.id == data['representative_id']), None)
            if found_rep_in_members:
                species_obj.representative = found_rep_in_members
            else: # Якщо старого представника немає серед поточних членів, вибираємо нового
                species_obj.update_representative()
        else:
             species_obj.representative = None # Якщо вид порожній

        return species_obj
    def get_parents(self, survival_threshold: float) -> list[Genome]:
        """
        Повертає список геномів, які виживають і можуть стати батьками.
        Це найкращі 'survival_threshold' * 100% геномів виду.
        Потребує попереднього сортування членів за фітнесом.

        Args:
            survival_threshold (float): Частка геномів, що виживають (напр., 0.2 для 20%).

        Returns:
            list[Genome]: Список геномів-батьків.
        """
        if not self.members:
            return []
        # Переконуємось, що відсортовано (хоча це зазвичай робиться раніше)
        # self.sort_members_by_fitness()
        num_survivors = max(1, int(math.ceil(len(self.members) * survival_threshold))) # Принаймні один виживає
        return self.members[:num_survivors]

    def __len__(self):
        """Повертає кількість членів у виді."""
        return len(self.members)

    def __repr__(self):
        """Повертає рядкове представлення виду для налагодження."""
        rep_id = self.representative.id if self.representative else "None"
        best_member_fit = self.members[0].fitness if self.members else -float('inf')
        return (f"Species(id={self.id}, members={len(self.members)}, "
                f"adj_fit_sum={self.total_adjusted_fitness:.3f}, "
                f"best_ever={self.best_fitness_ever:.3f}, "
                f"best_now={best_member_fit:.3f}, "
                f"stagnant={self.generations_since_improvement}, "
                f"offspring={self.offspring_count}, "
                f"rep_id={rep_id})")