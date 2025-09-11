# Configuration des Variables d'Environnement

## Fichier .env requis

Créez un fichier `.env` à la racine du projet avec les variables suivantes :

```bash
# Configuration de l'API
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Configuration Supabase (optionnel si déjà configuré)
VITE_SUPABASE_URL=your_supabase_url_here
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

## Instructions

1. Copiez le contenu ci-dessus dans un nouveau fichier nommé `.env` à la racine du projet
2. Modifiez `VITE_API_BASE_URL` selon votre environnement :
   - Développement local : `http://localhost:8000/api/v1`
   - Production : `https://votre-api.com/api/v1`
3. Redémarrez le serveur de développement après avoir créé le fichier `.env`

## Variables utilisées

- `VITE_API_BASE_URL` : URL de base de votre API (utilisée dans `apiStreaming.ts`, `FilePreviewDialog.tsx`, `FilePreviewSheet.tsx`)
- `VITE_SUPABASE_URL` : URL de votre instance Supabase
- `VITE_SUPABASE_ANON_KEY` : Clé anonyme Supabase

## Note importante

Le fichier `.env` ne doit pas être committé dans le repository pour des raisons de sécurité. Il est déjà ajouté au `.gitignore`.
