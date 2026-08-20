/**
 * domainLock.js — resolveAuthority() decide contra qué Authentik autentica
 * cada dominio público del chat.
 *
 * chat.teca.ca-smarts.com debe usar auth.teca.ca-smarts.com (mismo Authentik,
 * mismo provider "consulta-smart" y misma llave de firma que auth.casmart.internal
 * -- verificado en producción 2026-08-19 -- pero con certificado público real,
 * evitando el login "ciclado" que producía el certificado autofirmado interno
 * al fallar en silencio el fetch de fondo del intercambio de token). Cualquier
 * otro dominio (chat.casmart.internal, localhost, etc.) debe seguir usando el
 * Authentik interno de siempre.
 */
import { describe, it, expect } from 'vitest';
import { resolveAuthority, DOMAIN_AUTHORITY, DEFAULT_AUTHORITY } from '../../src/config/domainLock';

describe('resolveAuthority', () => {
    it('chat.teca.ca-smarts.com resuelve a auth.teca.ca-smarts.com', () => {
        expect(resolveAuthority('chat.teca.ca-smarts.com')).toBe(
            'https://auth.teca.ca-smarts.com/application/o/consulta-smart/'
        );
    });

    it('chat.casmart.internal (sin override) cae al Authentik interno de siempre', () => {
        expect(resolveAuthority('chat.casmart.internal')).toBe(DEFAULT_AUTHORITY);
    });

    it('un dominio desconocido (localhost, dev) también cae al default', () => {
        expect(resolveAuthority('localhost')).toBe(DEFAULT_AUTHORITY);
    });

    it('DOMAIN_AUTHORITY nunca apunta al mismo valor que DEFAULT_AUTHORITY (si algún día coincide, sobra la entrada)', () => {
        for (const authority of Object.values(DOMAIN_AUTHORITY)) {
            expect(authority).not.toBe(DEFAULT_AUTHORITY);
        }
    });
});
