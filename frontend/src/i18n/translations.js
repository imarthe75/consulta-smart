import React from 'react'

export const es = {
    // Auth
    auth: {
        login: 'Iniciar sesión',
        register: 'Registrarse',
        email: 'Correo Electrónico',
        password: 'Contraseña',
        username: 'Nombre de Usuario',
        logout: 'Cerrar sesión',
        notAccount: '¿No tienes cuenta?',
        haveAccount: '¿Ya tienes cuenta?',
        authError: 'Error de autenticación',
    },

    // Navigation
    nav: {
        chat: 'Chat',
        documents: 'Documentos',
        search: 'Búsqueda',
        consultarpp: 'ConsultaRPP',
        description: 'Sistema de Consultas Legales',
    },

    // Chat
    chat: {
        newSession: 'Nueva Sesión',
        selectSession: 'Selecciona o crea una nueva sesión',
        howCan: '¿Cómo puedo ayudarte hoy?',
        typing: 'Escribiendo...',
        askQuestion: 'Escribe tu pregunta aquí...',
        send: 'Enviar',
        sources: 'Fuentes',
        deleteSession: 'Eliminar sesión',
        sessionError: 'Error al crear sesión',
        messageError: 'Error al enviar mensaje',
    },

    // Documents
    documents: {
        title: 'Gestión de Documentos',
        upload: 'Carga un archivo',
        dragDrop: 'Arrastra un archivo aquí o haz clic para seleccionar',
        supportedFormats: 'Formatos soportados: PDF, Word, Imágenes',
        selectFile: 'Seleccionar archivo',
        category: 'Categoría del documento',
        categories: {
            reglamentos: 'Reglamentos',
            guias: 'Guías',
            tramites: 'Trámites',
            costos: 'Costos',
            otro: 'Otro',
        },
        uploaded: 'Documentos cargados',
        noDocuments: 'No hay documentos cargados aún.',
        processing: 'Procesando...',
        uploadError: 'Error al cargar archivo',
        invalidFormat: 'Formato de archivo no permitido. Solo PDF, Word e imágenes.',
        size: 'KB',
    },

    // Search
    search: {
        title: 'Búsqueda de Documentos',
        placeholder: 'Busca en documentos...',
        searchBtn: 'Buscar',
        noResults: 'No se encontraron resultados',
        makeSearch: 'Realiza una búsqueda para ver resultados',
        relevance: 'Relevancia',
    },

    // Messages
    messages: {
        success: 'Operación exitosa',
        error: 'Error',
        loading: 'Cargando...',
        noData: 'Sin datos disponibles',
    },

    // Profile
    profile: {
        user: 'Usuario',
        email: 'Correo',
    },
}

export default es
