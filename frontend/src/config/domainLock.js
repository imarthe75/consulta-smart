// Dominios públicos dedicados a un único tenant: el chat ignora `profile_id`
// de la URL y oculta el selector de temas, forzando siempre este perfil.
// Ver .agent/STATE.md para el contexto de por qué existe (dominio propio de "teca").
export const DOMAIN_LOCKED_PROFILE = {
    'chat.teca.ca-smarts.com': 'teca',
}

// Dominio de Authentik a usar según el dominio público del chat. auth.casmart.internal
// usa un certificado autofirmado (CA interna) -- un fetch de fondo (token exchange) a un
// host con cert no confiable falla en silencio y produce un login que "cicla" sin avisar
// por qué, a diferencia de la navegación completa al login, que sí deja aceptar el cert.
// auth.teca.ca-smarts.com es el MISMO Authentik (mismo provider "consulta-smart", misma
// llave de firma -- verificado 2026-08-19) pero con certificado público real, así que
// evita ese problema por completo además de dar el branding correcto. Default: el dominio
// interno de siempre, para no cambiar nada en local/dev ni en chat.casmart.internal.
export const DOMAIN_AUTHORITY = {
    'chat.teca.ca-smarts.com': 'https://auth.teca.ca-smarts.com/application/o/consulta-smart/',
}
export const DEFAULT_AUTHORITY = 'https://auth.casmart.internal/application/o/consulta-smart/'

export function resolveAuthority(hostname) {
    return DOMAIN_AUTHORITY[hostname] || DEFAULT_AUTHORITY
}
