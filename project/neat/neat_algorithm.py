# neat/neat_algorithm.py

import pickle
import random
import math
import copy
import itertools
from concurrent.futures import ProcessPoolExecutor, as_completed # Додаємо імпорт
import os # Для os.cpu_count

from .genome import Genome
from .innovation import InnovationManager
from .species import Species

class NeatAlgorithm:
    """
    Клас, що реалізує основний цикл алгоритму NEAT:
    Оцінка -> Видоутворення -> Відбір -> Розмноження (Кросовер + Мутація).
    """

    def __init__(self, config: dict, num_inputs: int, num_outputs: int, initial_genome_id_start=0, _is_loading=False):
        # ... (поточний код __init__)
        self.config = config
        self._genome_id_counter = itertools.count(initial_genome_id_start)
        self.population_size = config.get('POPULATION_SIZE', 150)
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.species_representatives_prev_gen: dict[int, Genome] = {} # {species_id: representative_genome}
        self.generation_statistics: list[dict] = [] # Для збереження історії
        required_keys = [
            'POPULATION_SIZE', 'COMPATIBILITY_THRESHOLD', 'C1_EXCESS',
            'C2_DISJOINT', 'C3_WEIGHT', 'WEIGHT_MUTATE_RATE',
            'WEIGHT_REPLACE_RATE', 'WEIGHT_MUTATE_POWER', 'WEIGHT_CAP',
            'WEIGHT_INIT_RANGE', 'ADD_CONNECTION_RATE', 'ADD_NODE_RATE',
            'ELITISM', 'SELECTION_PERCENTAGE', 'CROSSOVER_RATE',
            'MAX_STAGNATION', 'INHERIT_DISABLED_GENE_RATE'
        ]
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
             raise ValueError(f"Missing required configuration key(s) in config: {', '.join(missing_keys)}")
        node_id_for_innov_manager = num_inputs + num_outputs + 1 # inputs + outputs + bias
        # initial_node_id_count = num_inputs + num_outputs + 1
        initial_innov_count = (num_inputs + 1) * num_outputs
        self.innovation_manager = InnovationManager(
            start_node_id=node_id_for_innov_manager,
            start_innovation_num=0 # Починаємо з 0, Genome.__init__ використає менеджер
        )

        # === ПОВЕРТАЄМО ЛІЧИЛЬНИК ID ===
        self._genome_id_counter = itertools.count(0) # Глобальний лічильник ID геномів
        # ===============================

        self.population = self._create_initial_population(self.innovation_manager)
        self.species = []
        self.generation = 0
        self.best_genome_overall = None
        self._speciate_population()
        if not _is_loading:
            self.population = self._create_initial_population(self.innovation_manager)
            self._speciate_population() # Перше видоутворення використовує випадкових представників з поточної популяції
            self._update_previous_gen_representatives() # Зберігаємо представників для наступного покоління
    
    def _update_previous_gen_representatives(self):
        """Оновлює словник представників попереднього покоління."""
        self.species_representatives_prev_gen.clear()
        for spec in self.species:
            if spec and spec.representative: # spec.representative вже має бути встановлений
                # Важливо: зберігаємо копію, щоб мутації в наступному поколінні не вплинули на старого представника
                self.species_representatives_prev_gen[spec.id] = spec.representative.copy()
    # === ПОВЕРТАЄМО МЕТОД ОТРИМАННЯ ID ===
    def _get_next_genome_id(self) -> int:
        """Повертає наступний унікальний ID геному."""
        return next(self._genome_id_counter)
    # ====================================

    # --- Решта методів класу NeatAlgorithm без змін ---
    # (залишаємо _create_initial_population, _speciate_population, і т.д. як були)
    def _create_initial_population(self, innovation_manager: InnovationManager) -> list[Genome]: # Приймає менеджер
        """Створює початкову популяцію геномів."""
        population = []
        for _ in range(self.population_size):
            genome_id = self._get_next_genome_id()
            # Передаємо той самий менеджер інновацій кожному новому геному
            genome = Genome(genome_id, self.num_inputs, self.num_outputs, self.config, innovation_manager)
            population.append(genome)
        # Після створення всієї популяції, лічильник інновацій в менеджері буде актуальним
        print(f"Initial population created. Next innovation number: {innovation_manager.innovation_counter}")
        return population

    def _get_next_genome_id(self) -> int: # Переконайтесь, що цей метод є
        """Повертає наступний унікальний ID геному."""
        return next(self._genome_id_counter)
    
    def get_state_data(self) -> dict:
        """Збирає дані для збереження стану NEAT, забезпечуючи консистентність."""
        print("DEBUG SAVE: Entered get_state_data.")
        
        # Збираємо всі унікальні геноми, на які є посилання
        relevant_genomes_map = {} # Використовуємо словник для унікальності за ID

        # 1. Геноми з поточної популяції (це популяція для НАСТУПНОЇ генерації, P_N+1)
        for g in self.population: # self.population тут - це вже next_population
            if g and g.id not in relevant_genomes_map:
                relevant_genomes_map[g.id] = g

        # 2. Геноми з членів поточних видів (це види S_N, їх члени - з популяції P_N)
        # Ці геноми можуть бути відсутні в self.population, якщо вони не пройшли у наступне покоління
        for spec in self.species:
            if spec:
                if spec.representative and spec.representative.id not in relevant_genomes_map:
                    relevant_genomes_map[spec.representative.id] = spec.representative
                for member in spec.members:
                    if member and member.id not in relevant_genomes_map:
                        relevant_genomes_map[member.id] = member
        
        # 3. Геноми з представників попереднього покоління (використовувались для видоутворення S_N, самі з P_N-1)
        for rep_genome in self.species_representatives_prev_gen.values():
            if rep_genome and rep_genome.id not in relevant_genomes_map:
                relevant_genomes_map[rep_genome.id] = rep_genome

        # 4. Найкращий геном за весь час
        if self.best_genome_overall and self.best_genome_overall.id not in relevant_genomes_map:
            relevant_genomes_map[self.best_genome_overall.id] = self.best_genome_overall
        
        # Зберігаємо копії всіх цих релевантних геномів
        # Це гарантує, що всі ID, на які посилатимуться species_data та prev_gen_reps, будуть доступні при завантаженні
        all_referenced_genomes_copies = [g.copy() for g in relevant_genomes_map.values() if g]
        print(f"DEBUG SAVE: Total unique relevant genomes to save in 'population_genomes': {len(all_referenced_genomes_copies)}")

        # Дані про види (species_state_data) беруться з поточного self.species (S_N)
        species_state_data_to_save = [spec.get_state_data() for spec in self.species if spec]
        
        # ID представників попереднього покоління (для видоутворення S_N)
        prev_gen_reps_data_ids = {
            spec_id: rep_g.id 
            for spec_id, rep_g in self.species_representatives_prev_gen.items() 
            if rep_g
        }

        # Зберігаємо ID поточної популяції (P_N+1), щоб знати, яку популяцію активувати після завантаження
        current_active_population_ids = [g.id for g in self.population if g]

        state = {
            'generation': self.generation, # Поточна завершена генерація N
            'best_genome_overall': self.best_genome_overall.copy() if self.best_genome_overall else None,
            'innovation_manager_state': {
                '_next_node_id': self.innovation_manager._next_node_id,
                '_next_innovation_num': self.innovation_manager._next_innovation_num,
            },
            # Це поле тепер містить ВСІ геноми, необхідні для відновлення стану (P_N+1, P_N, P_N-1)
            'population_genomes': all_referenced_genomes_copies, 
            # Зберігаємо ID активної популяції, яка має бути self.population після завантаження
            'current_active_population_ids': current_active_population_ids,
            'species_state_data': species_state_data_to_save, 
            '_genome_id_counter_val': next(self._genome_id_counter) - 1,
            '_max_used_species_id': max((s.id for s in self.species if s), default=0),
            'species_representatives_prev_gen_ids': prev_gen_reps_data_ids,
            'generation_statistics': self.generation_statistics
        }
        print(f"DEBUG SAVE: Max species ID being saved: {state['_max_used_species_id']}")
        print(f"DEBUG SAVE: Genome counter value being saved: {state['_genome_id_counter_val']}")
        print(f"DEBUG SAVE: Saving {len(state['population_genomes'])} total genomes, {len(state['current_active_population_ids'])} active population genomes.")
        return state

    
    @classmethod
    def load_from_state_data(cls, state_data: dict, config: dict, num_inputs: int, num_outputs: int) -> 'NeatAlgorithm':
        initial_genome_id_to_set = state_data.get('_genome_id_counter_val', -1) + 1
        neat = cls(config, num_inputs, num_outputs, initial_genome_id_start=initial_genome_id_to_set, _is_loading=True)

        neat.generation = state_data['generation']
        
        best_genome_overall_data = state_data.get('best_genome_overall')
        if best_genome_overall_data:
            neat.best_genome_overall = best_genome_overall_data
        else:
            neat.best_genome_overall = None

        im_state = state_data['innovation_manager_state']
        neat.innovation_manager._next_node_id = im_state['_next_node_id']
        neat.innovation_manager._next_innovation_num = im_state['_next_innovation_num']
        neat.innovation_manager.reset_generation_history()

        # Завантажуємо ВСІ збережені геноми в загальну карту
        all_loaded_genomes_list = state_data.get('population_genomes', [])
        genomes_by_id = {genome.id: genome for genome in all_loaded_genomes_list if genome}
        print(f"Info (Load): Loaded {len(all_loaded_genomes_list)} total genomes into master list. Genomes by ID map created with {len(genomes_by_id)} entries.")

        # Відновлюємо АКТИВНУ популяцію (P_N+1)
        current_active_population_ids = state_data.get('current_active_population_ids', [])
        neat.population = [genomes_by_id[gid] for gid in current_active_population_ids if gid in genomes_by_id]
        print(f"Info (Load): Reconstructed active population with {len(neat.population)} genomes.")


        max_loaded_species_id = state_data.get('_max_used_species_id', 0)
        Species._species_counter = itertools.count(max_loaded_species_id + 1)
        print(f"Info (Load): Species ID counter reset to start from {max_loaded_species_id + 1}.")
        
        neat.species = []
        loaded_species_data = state_data.get('species_state_data', [])
        print(f"Info (Load): Attempting to load {len(loaded_species_data)} species records.")

        for s_data in loaded_species_data:
            species_id_from_data = s_data.get('id', 'Unknown_ID')
            representative_genome_obj = None
            rep_id = s_data.get('representative_id')
            member_ids_from_data = s_data.get('member_ids', [])
            
            # print(f"Debug (Load): Processing species data for ID {species_id_from_data}. Rep ID: {rep_id}. Member IDs: {member_ids_from_data}")

            if rep_id is not None:
                representative_genome_obj = genomes_by_id.get(rep_id)
                if not representative_genome_obj:
                    print(f"Warning (Load): Representative genome with ID '{rep_id}' for species '{species_id_from_data}' not found in loaded master genomes list.")

            if not representative_genome_obj and member_ids_from_data:
                # print(f"Info (Load): Rep ID '{rep_id}' for species '{species_id_from_data}' not found or was None. Attempting to find representative from its members.")
                for m_id_fallback in member_ids_from_data:
                    fallback_rep_obj = genomes_by_id.get(m_id_fallback)
                    if fallback_rep_obj:
                        representative_genome_obj = fallback_rep_obj
                        print(f"Info (Load): Using member ID '{m_id_fallback}' as representative for species '{species_id_from_data}'.")
                        break 
            
            if not representative_genome_obj:
                 print(f"Error (Load): Could not assign a representative for species ID '{species_id_from_data}'. Skipping this species.")
                 continue

            species_obj = Species(representative_genome_obj) 
            species_obj.id = species_id_from_data 
            species_obj.generations_since_improvement = s_data.get('generations_since_improvement', 0)
            species_obj.best_fitness_ever = s_data.get('best_fitness_ever', 0.0)
            species_obj.offspring_count = s_data.get('offspring_count', 0)
            
            species_obj.clear_members() 
            
            actually_added_members_count = 0
            for member_id in member_ids_from_data:
                member_genome = genomes_by_id.get(member_id)
                if member_genome:
                    species_obj.add_member(member_genome) 
                    actually_added_members_count += 1
                # else:
                    # print(f"Warning (Load): Member genome with ID '{member_id}' for species '{species_obj.id}' not found in loaded master genomes list.") 
            
            if actually_added_members_count > 0:
                # Представник вже встановлений конструктором Species як копія representative_genome_obj.
                # Якщо потрібно, щоб представник був тим самим об'єктом, що і член популяції:
                # found_rep_in_members = genomes_by_id.get(rep_id)
                # if found_rep_in_members and found_rep_in_members in species_obj.members:
                #    species_obj.representative = found_rep_in_members
                # else:
                #    # Залишаємо копію, або вибираємо нового, якщо старий не серед членів
                #    if not any(m.id == species_obj.representative.id for m in species_obj.members) and species_obj.members:
                #        species_obj.update_representative()


                neat.species.append(species_obj)
                # print(f"Info (Load): Successfully loaded species ID '{species_obj.id}' with {actually_added_members_count} members. Representative ID: {species_obj.representative.id if species_obj.representative else 'None'}.")
            else:
                print(f"Warning (Load): Species ID '{species_id_from_data}' was skipped because no valid members could be loaded from member_ids: {member_ids_from_data}.")
        
        print(f"Info (Load): Finished loading species. Total species loaded: {len(neat.species)}.")

        neat.species_representatives_prev_gen = {}
        prev_gen_reps_ids_data = state_data.get('species_representatives_prev_gen_ids', {})
        # print(f"Info (Load): Attempting to load {len(prev_gen_reps_ids_data)} previous generation representatives.")
        for spec_id, rep_id_prev in prev_gen_reps_ids_data.items():
            rep_genome_prev = genomes_by_id.get(rep_id_prev)
            if rep_genome_prev:
                neat.species_representatives_prev_gen[spec_id] = rep_genome_prev
            # else:
                # print(f"Warning (Load): Could not find genome for saved previous representative ID '{rep_id_prev}' of species_id_key '{spec_id}'.")
        # print(f"Info (Load): Loaded {len(neat.species_representatives_prev_gen)} previous generation representatives.")
        
        neat.generation_statistics = state_data.get('generation_statistics', [])

        print(f"NEAT state loaded. Gen: {neat.generation}, Pop: {len(neat.population)}, Species: {len(neat.species)}, PrevReps: {len(neat.species_representatives_prev_gen)}")
        return neat
    
    def _speciate_population(self):
        """
        Розподіляє геноми по видах на основі генетичної відстані,
        використовуючи представників з ПОПЕРЕДНЬОГО покоління (якщо доступні).
        """
        threshold = self.config['COMPATIBILITY_THRESHOLD']
        c1 = self.config['C1_EXCESS']
        c2 = self.config['C2_DISJOINT']
        c3 = self.config['C3_WEIGHT']

        # Використовуємо представників з попереднього покоління, якщо це не перше покоління
        # або якщо species_representatives_prev_gen не порожній (наприклад, після завантаження)
        representatives_to_use = {}
        if self.generation > 0 and self.species_representatives_prev_gen:
            # Перевіряємо, чи ID видів з попереднього покоління все ще актуальні
            # (деякі види могли зникнути)
            # Створюємо тимчасовий список видів, які існували
            existing_species_for_repopulation = []
            for spec_id, rep_genome in self.species_representatives_prev_gen.items():
                # Створюємо "пустий" вид лише для утримання представника
                # Фактичні члени будуть додані нижче
                temp_spec = Species(rep_genome.copy()) # Використовуємо копію представника
                temp_spec.id = spec_id
                temp_spec.representative = rep_genome # Встановлюємо збереженого представника
                existing_species_for_repopulation.append(temp_spec)
            species_to_compare_against = existing_species_for_repopulation
            print(f"Speciation: Using {len(species_to_compare_against)} representatives from previous generation.")
        else:
            # Для першого покоління або якщо немає збережених представників,
            # використовуємо поточні види (які на цьому етапі будуть порожніми,
            # або матимуть одного члена, якщо це самий початок).
            # Або, для самого першого видоутворення, ми можемо не мати self.species.
            # У цьому випадку, перший геном створює перший вид.
            species_to_compare_against = [] # Будуть створюватися нові види
            if not self.species and self.population: # Дуже перший запуск
                 print("Speciation: Initial speciation, no previous representatives.")
            elif self.species: # Якщо види є, але немає попередніх представників (напр. після завантаження без них)
                 # Очистимо їх членів і використаємо поточних представників (якщо вони є)
                 for spec in self.species:
                     if spec.representative: # Якщо представник був відновлений
                         species_to_compare_against.append(spec)
                         spec.clear_members() # Очищаємо для нового наповнення
                     else: # Вид без представника не може використовуватись для порівняння
                         print(f"Warning: Species {spec.id} has no representative during speciation, will likely be removed.")
                 print(f"Speciation: Using {len(species_to_compare_against)} current representatives (e.g., after load).")


        newly_created_species_this_gen = []
        final_species_list = list(species_to_compare_against) # Починаємо з видів, що мають представників

        for genome in self.population:
            if not genome: continue

            assigned_to_existing = False
            for spec in species_to_compare_against: # Порівнюємо зі "старими" представниками
                if not spec.representative: continue # Про всяк випадок
                distance = genome.distance(spec.representative, c1, c2, c3)
                if distance < threshold:
                    spec.add_member(genome) # add_member оновить genome.species_id
                    assigned_to_existing = True
                    break
            
            if not assigned_to_existing:
                # Якщо не підійшов до жодного існуючого, перевіряємо щойно створені в цьому поколінні
                assigned_to_newly_created = False
                for new_spec in newly_created_species_this_gen:
                    # Представник new_spec - це перший геном, що його утворив
                    distance = genome.distance(new_spec.representative, c1, c2, c3)
                    if distance < threshold:
                        new_spec.add_member(genome)
                        assigned_to_newly_created = True
                        break
                if not assigned_to_newly_created:
                    # Створюємо абсолютно новий вид
                    brand_new_species = Species(genome) # genome стає представником
                    newly_created_species_this_gen.append(brand_new_species)
                    final_species_list.append(brand_new_species)


        # Оновлюємо self.species: видаляємо порожні види з existing_species_for_repopulation
        # та додаємо newly_created_species_this_gen (вони не можуть бути порожніми)
        self.species = [s for s in final_species_list if s.members]

        # Після того, як всі геноми поточного покоління розподілені,
        # оновлюємо представників КОЖНОГО виду для використання в НАСТУПНОМУ поколінні.
        # Це робиться ВИПАДКОВИМ вибором з поточних членів.
        for spec in self.species:
            spec.update_representative() # Тепер це правильно, бо це для НАСТУПНОГО порівняння

    def _calculate_adjusted_fitness(self):
        for spec in self.species:
            spec.calculate_adjusted_fitness_and_sum()

    def _determine_num_offspring(self) -> dict[int, int]:
        num_offspring_map = {}
        # Важливо: використовуємо скориговану суму фітнесу з об'єктів Species
        total_adjusted_fitness_sum = sum(spec.total_adjusted_fitness for spec in self.species if spec.total_adjusted_fitness > 0)

        if total_adjusted_fitness_sum <= 0:
            # Якщо всі фітнеси нульові або видів немає, ділимо порівну
            num_active_species = len(self.species)
            if not num_active_species: return {}
            base_offspring = self.population_size // num_active_species
            remainder = self.population_size % num_active_species
            active_species_list = [spec for spec in self.species] # Створюємо список для індексації
            for i, spec in enumerate(active_species_list):
                 count = base_offspring + (1 if i < remainder else 0)
                 num_offspring_map[spec.id] = count
                 spec.offspring_count = count # Зберігаємо в об'єкті виду
            return num_offspring_map

        # Розрахунок пропорційно до скоригованого фітнесу
        total_spawn = 0
        spawn_fractions = {}
        for spec in self.species:
             if spec.total_adjusted_fitness > 0:
                 proportion = spec.total_adjusted_fitness / total_adjusted_fitness_sum
                 spawn_amount_float = proportion * self.population_size
                 num_offspring_map[spec.id] = int(spawn_amount_float)
                 spawn_fractions[spec.id] = spawn_amount_float - int(spawn_amount_float)
                 total_spawn += int(spawn_amount_float)
             else:
                  num_offspring_map[spec.id] = 0
             spec.offspring_count = num_offspring_map.get(spec.id, 0) # Оновлюємо лічильник в виді

        # Розподіляємо залишок на основі дробової частини
        spawn_diff = self.population_size - total_spawn
        if spawn_diff > 0:
             sorted_species_by_fraction = sorted(spawn_fractions.items(), key=lambda item: item[1], reverse=True)
             for i in range(min(spawn_diff, len(sorted_species_by_fraction))):
                 spec_id_to_increment = sorted_species_by_fraction[i][0]
                 num_offspring_map[spec_id_to_increment] += 1
                 # Оновлюємо лічильник і в об'єкті виду
                 spec = next((s for s in self.species if s.id == spec_id_to_increment), None)
                 if spec: spec.offspring_count += 1

        return num_offspring_map


    def _handle_stagnation(self):
         species_to_keep = []
         max_stagnation = self.config.get('MAX_STAGNATION', 15)
         num_non_stagnant = 0
         # Спочатку оновлюємо стагнацію для всіх
         for spec in self.species:
             spec.update_stagnation_and_best_fitness()
             if spec.generations_since_improvement <= max_stagnation:
                  num_non_stagnant += 1

         can_remove_stagnant = num_non_stagnant >= 2 # Дозволяємо видаляти, якщо є хоча б 2 не-стагнуючих види

         kept_species_ids = set()
         if not self.species: return # Якщо видів немає, нічого робити

         # Завжди зберігаємо найкращий вид, навіть якщо він стагнує
         best_overall_species = max(self.species, key=lambda s: s.best_fitness_ever, default=None)

         for spec in self.species:
             is_stagnant = spec.generations_since_improvement > max_stagnation
             should_keep = False
             if spec == best_overall_species: # Завжди зберігаємо найкращий
                 should_keep = True
             elif not is_stagnant: # Зберігаємо не стагнуючі
                  should_keep = True
             elif not can_remove_stagnant: # Якщо не можна видаляти стагнуючі, зберігаємо
                  should_keep = True

             if should_keep:
                  species_to_keep.append(spec)
                  kept_species_ids.add(spec.id)
             else:
                  print(f"Species {spec.id} removed due to stagnation ({spec.generations_since_improvement} gens).")

         # Якщо після видалення залишився лише один вид (який міг бути стагнуючим, але був найкращим),
         # а інші стагнуючі були видалені, можемо спробувати додати назад один стагнуючий,
         # щоб підтримати різноманіття (опціонально)
         # ... (можна додати цю логіку, якщо потрібно)

         self.species = species_to_keep
         print(f"Species after stagnation handling: {[s.id for s in self.species]}")



    def _reproduce(self) -> list[Genome]:
        next_population = []
        survival_threshold = self.config.get('SELECTION_PERCENTAGE', 0.2)
        prob_crossover = self.config.get('CROSSOVER_RATE', 0.75)
        elitism_count = self.config.get('ELITISM', 1)

        self._handle_stagnation() # забираємо стагнуючі види з пулу для розмноження
        num_offspring_map = self._determine_num_offspring() 

        if not self.species:
             print("Error: No species left to reproduce. Resetting population.")
             # Передаємо менеджер інновацій при перестворенні
             return self._create_initial_population(self.innovation_manager)
        
        all_parents_list = [] # Для заповнення популяції, якщо не вистачає
        for spec in self.species:
             all_parents_list.extend(spec.members)

        for spec in self.species:
            spawn_amount = spec.offspring_count
            if spawn_amount == 0 or not spec.members: continue

            spec.sort_members_by_fitness()
            elites_added = 0
            if elitism_count > 0:
                for i in range(min(elitism_count, spawn_amount, len(spec.members))):
                     elite_copy = spec.members[i].copy()
                     # --- Важливо: Елітам теж треба дати новий ID ---
                     elite_copy.id = self._get_next_genome_id()
                     next_population.append(elite_copy)
                     elites_added += 1
            spawn_amount -= elites_added

            if spawn_amount == 0: continue

            parents = spec.get_parents(survival_threshold)
            if not parents: parents = spec.members[:1] # Якщо всі погані, беремо найкращого
            if not parents: continue # Якщо вид порожній (не має статися)

            while spawn_amount > 0:
                 parent1 = random.choice(parents)
                 child = None
                 if random.random() < prob_crossover and len(parents) > 1:
                     parent2 = random.choice(parents)
                     attempts = 0
                     while parent2.id == parent1.id and attempts < 5 and len(parents) > 1:
                         parent2 = random.choice(parents)
                         attempts += 1
                     g1_is_fitter = parent1.fitness > parent2.fitness
                     child = self._crossover_with_innovation_manager(parent1, parent2, g1_is_fitter)
                 else:
                     child = parent1.copy()

                 child.id = self._get_next_genome_id() # Тепер цей метод існує
                 # Мутації
                 child.mutate_weights()
                 if random.random() < self.config['ADD_CONNECTION_RATE']:
                     child.mutate_add_connection(self.innovation_manager)
                 if random.random() < self.config['ADD_NODE_RATE']:
                     child.mutate_add_node(self.innovation_manager)

                 next_population.append(child)
                 spawn_amount -= 1

        current_pop_size = len(next_population)
        if current_pop_size < self.population_size:
             all_parents_list.sort(key=lambda g: g.fitness, reverse=True) # Сортуємо всіх батьків
             needed = self.population_size - current_pop_size
             fill_idx = 0
             while needed > 0 and all_parents_list:
                 filler_parent = all_parents_list[fill_idx % len(all_parents_list)]
                 if filler_parent:
                     filler = filler_parent.copy()
                     filler.id = self._get_next_genome_id()
                     # Можна застосувати невелику мутацію ваг до заповнювачів
                     filler.mutate_weights()
                     next_population.append(filler)
                     needed -= 1
                 fill_idx += 1
             # Якщо батьків не вистачило, створюємо повністю нові
             while len(next_population) < self.population_size:
                  new_genome = Genome(self._get_next_genome_id(), self.num_inputs, self.num_outputs, self.config, self.innovation_manager)
                  next_population.append(new_genome)


        elif current_pop_size > self.population_size:
             # Обрізаємо, якщо згенерували забагато (малоймовірно при правильному розрахунку)
             next_population = next_population[:self.population_size]


        return next_population

    def _crossover_with_innovation_manager(self, parent1: Genome, parent2: Genome, g1_is_fitter: bool) -> Genome:
        """Виконує кросовер з правильним innovation_manager."""
        # Тимчасово зберігаємо innovation_manager в геномах
        parent1._innovation_manager = self.innovation_manager
        parent2._innovation_manager = self.innovation_manager
        
        # Виконуємо кросовер
        child = Genome.crossover(parent1, parent2, g1_is_fitter)
        
        # Видаляємо тимчасові посилання
        if hasattr(parent1, '_innovation_manager'):
            delattr(parent1, '_innovation_manager')
        if hasattr(parent2, '_innovation_manager'):
            delattr(parent2, '_innovation_manager')
        
        return child
    def run_generation(self, evaluation_function): # evaluation_function тепер глобальна
        """Запускає один цикл покоління з паралельною оцінкою."""
        self.generation += 1
        self.innovation_manager.reset_generation_history()

        total_fitness = 0.0
        max_fitness = -float('inf')
        current_best_genome = None
        evaluation_results = {}

        # --- Паралельна оцінка фітнесу ---
        population_to_evaluate = [(g.id, g) for g in self.population if g] # Список кортежів (id, genome)
        num_processes = self.config.get('NUM_PROCESSES', os.cpu_count()) # Кількість процесів

        print(f"Starting parallel evaluation for {len(population_to_evaluate)} genomes using {num_processes} processes...")
        futures = {}
        # Використовуємо ProcessPoolExecutor
        # Важливо: передаємо КОПІЮ self.config, щоб уникнути проблем із спільним доступом
        config_copy = self.config.copy()
        try:
            with ProcessPoolExecutor(max_workers=num_processes) as executor:
                # Надсилаємо завдання: evaluate_single_genome(genome_tuple, config)
                for genome_tuple in population_to_evaluate:
                    future = executor.submit(evaluation_function, genome_tuple, config_copy)
                    # Зберігаємо future та відповідний ID геному
                    futures[future] = genome_tuple[0] # Ключ - future, значення - genome_id

                # Збираємо результати по мірі завершення
                for future in as_completed(futures):
                    genome_id = futures[future]
                    try:
                        _, fitness = future.result() # Отримуємо результат (id, fitness)
                        evaluation_results[genome_id] = fitness
                    except Exception as exc:
                        print(f'Genome {genome_id} evaluation generated an exception: {exc}')
                        evaluation_results[genome_id] = 0.001 # Мінімальний фітнес при помилці
        except Exception as pool_exc:
             print(f"Error during ProcessPoolExecutor execution: {pool_exc}")
             # Якщо пул не запустився, оцінюємо послідовно як запасний варіант
             for genome_id, genome in population_to_evaluate:
                 try:
                     _, fitness = evaluation_function((genome_id, genome), config_copy)
                     evaluation_results[genome_id] = fitness
                 except Exception as eval_exc:
                      print(f"Sequential evaluation error for genome {genome_id}: {eval_exc}")
                      evaluation_results[genome_id] = 0.001
        # ------------------------------------

        # Оновлюємо фітнес в геномах поточної популяції
        valid_evaluated_genomes = 0
        for genome in self.population:
             if genome:
                  genome.fitness = evaluation_results.get(genome.id, 0.001)
                  total_fitness += genome.fitness
                  valid_evaluated_genomes += 1
                  if genome.fitness > max_fitness:
                       max_fitness = genome.fitness
                       current_best_genome = genome # Зберігаємо посилання на кращий геном

        avg_fitness = total_fitness / valid_evaluated_genomes if valid_evaluated_genomes > 0 else 0.0

        # Оновлюємо найкращий геном за весь час
        if self.best_genome_overall is None or (current_best_genome and current_best_genome.fitness > self.best_genome_overall.fitness):
            # Копіюємо кращий геном, щоб зберегти його стан на цей момент
            self.best_genome_overall = current_best_genome.copy() if current_best_genome else None

        # --- Наступні кроки NEAT ---
        # Оновлюємо статистику перед тим, як _speciate_population змінить self.species
        stats = {
            "generation": self.generation,
            "max_fitness": max_fitness if max_fitness > -float('inf') else None,
            "average_fitness": avg_fitness,
            "num_species": len(self.species), # Кількість видів ДО перевидоутворення
            "best_genome_current_gen": current_best_genome,
            "best_genome_overall": self.best_genome_overall
        }
        # Зберігаємо представників поточних видів ПЕРЕД тим, як _speciate_population їх потенційно змінить
        self._update_previous_gen_representatives() # <--- ВАЖЛИВО

        self._speciate_population() # Тепер використовує self.species_representatives_prev_gen
        # >>> ВАЖЛИВЕ ДОДАВАННЯ: Сортуємо членів кожного виду ПІСЛЯ видоутворення <<<
        for spec in self.species:
            if spec.members: # Перевірка, чи є члени для сортування
                spec.sort_members_by_fitness()
        # >>> КІНЕЦЬ ДОДАВАННЯ <<<
        self._calculate_adjusted_fitness()
        next_population = self._reproduce()
        self.population = next_population
        stats["num_species_after_speciation"] = len(self.species)
        self.generation_statistics.append(stats) # Зберігаємо фінальну статистик
        # Повертаємо статистику
        return stats

    def get_best_genome_overall(self) -> Genome | None:
        return self.best_genome_overall