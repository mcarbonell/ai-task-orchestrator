# Project Context: Tienda E-commerce

## Descripción General
Aplicación web de e-commerce con catálogo de productos, carrito de compras y checkout.

## Stack Tecnológico

### Frontend
- Framework: React 18 con TypeScript
- Build: Vite
- Estilos: Tailwind CSS
- Estado: Zustand
- Testing: Vitest + React Testing Library
- Routing: React Router v6

### Backend (API Mock)
- json-server para desarrollo

## Convenciones de Código

### Estructura de Archivos
```
src/
├── components/         # Componentes reutilizables
│   ├── ui/             # Componentes base (Button, Input, etc.)
│   └── features/       # Componentes de negocio
├── pages/              # Páginas de la aplicación
├── hooks/              # Custom hooks
├── store/              # Estado global (Zustand)
├── types/              # Tipos TypeScript
└── utils/              # Utilidades
```

### Estilo de Código
- Usar TypeScript estricto
- Componentes funcionales con hooks
- Props interfaces en el mismo archivo
- Usar `const` en lugar de `function` para componentes
- Importar React solo cuando se use JSX transform

## Comandos Útiles
```bash
# Instalar dependencias
npm install

# Desarrollo
npm run dev

# Tests
npm test

# Build
npm run build

# Preview build
npm run preview
```

## Notas para IAs
- El proyecto usa Vite, no Create React App
- json-server corre en puerto 3001
- Usar React Router v6 (useNavigate, useParams)
- Tailwind ya está configurado
- No modificar vite.config.ts sin consultar
