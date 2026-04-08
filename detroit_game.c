#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_LINE 1024
#define MAX_CHOICES 10
#define SAVE_FILE "savegame.txt"

// Structure d'un choix
typedef struct {
    char text[MAX_LINE];
    char link[MAX_LINE]; // L'ID de la page de destination
} Choice;

// Structure d'une page (chapitre)
typedef struct {
    char id[MAX_LINE];
    char title[MAX_LINE];
    char text[4096];
    Choice choices[MAX_CHOICES];
    int num_choices;
} Page;

// Fonction pour nettoyer une chaîne (enlever les espaces et \n au début et à la fin)
void trim_string(char *str) {
    char *end;
    while(isspace((unsigned char)*str)) str++;
    if(*str == 0) return;
    end = str + strlen(str) - 1;
    while(end > str && isspace((unsigned char)*end)) end--;
    end[1] = '\0';
}

// Fonction de Sauvegarde
void save_game(const char* current_page_id) {
    FILE *f = fopen(SAVE_FILE, "w");
    if (f == NULL) {
        printf("\n[Erreur] Impossible de créer la sauvegarde.\n");
        return;
    }
    fprintf(f, "%s\n", current_page_id);
    fclose(f);
    printf("\n[Succès] Partie sauvegardée avec succès !\n");
}

// Fonction de Chargement
int load_game(char* current_page_id) {
    FILE *f = fopen(SAVE_FILE, "r");
    if (f == NULL) {
        printf("\n[Erreur] Aucune sauvegarde trouvée.\n");
        return 0;
    }
    if (fgets(current_page_id, MAX_LINE, f) != NULL) {
        trim_string(current_page_id);
        fclose(f);
        printf("\n[Succès] Partie chargée !\n");
        return 1;
    }
    fclose(f);
    return 0;
}

// Fonction de recherche de page par ID (corrige le problème des liens)
int find_page_index(Page *pages, int total_pages, const char *target_id) {
    char clean_target[MAX_LINE];
    strcpy(clean_target, target_id);
    trim_string(clean_target);
    
    for (int i = 0; i < total_pages; i++) {
        char clean_current[MAX_LINE];
        strcpy(clean_current, pages[i].id);
        trim_string(clean_current);
        
        if (strcmp(clean_current, clean_target) == 0) {
            return i;
        }
    }
    return -1; // Page non trouvée
}

// Boucle principale du jeu (extrait)
void play_game(Page *pages, int total_pages, const char *start_id) {
    char current_id[MAX_LINE];
    strcpy(current_id, start_id);
    
    while (1) {
        int page_idx = find_page_index(pages, total_pages, current_id);
        if (page_idx == -1) {
            printf("\n[Erreur] Lien brisé : Impossible de trouver la page '%s'.\n", current_id);
            break;
        }
        
        Page *p = &pages[page_idx];
                
        // Affichage de la page
        printf("\n====================================================\n");
        printf("%s\n", p->title);
        printf("====================================================\n");
        printf("%s\n\n", p->text);
        
        if (p->num_choices == 0) {
            printf("\n--- FIN DE L'HISTOIRE ---\n");
            break;
        }
        
        // Affichage des choix et des options système
        for (int i = 0; i < p->num_choices; i++) {
            printf("%d. %s\n", i + 1, p->choices[i].text);
        }
        printf("S. Sauvegarder la partie\n");
        printf("C. Charger la partie\n");
        printf("Q. Quitter\n");
        
        // Demander le choix du joueur
        char input[10];
        printf("\nVotre choix : ");
        if (fgets(input, sizeof(input), stdin) == NULL) break;
        trim_string(input);
        
        if (strcasecmp(input, "Q") == 0) {
            printf("Merci d'avoir joué !\n");
            break;
        } else if (strcasecmp(input, "S") == 0) {
            save_game(current_id);
        } else if (strcasecmp(input, "C") == 0) {
            load_game(current_id); // Modifie l'ID courant
        } else {
            // Logique de choix classique
            int choice_num = atoi(input);
            if (choice_num > 0 && choice_num <= p->num_choices) {
                // IMPORTANT: Met à jour l'ID courant avec le lien du choix
                strcpy(current_id, p->choices[choice_num - 1].link);
                trim_string(current_id); // Sécurité supplémentaire
            } else {
                printf("Choix invalide. Veuillez réessayer.\n");
            }
        }
    }
}