/**
 * DocumentUpload Component Tests
 *
 * Reescrito 2026-08-14: la versión anterior probaba una API imaginaria del
 * store (`uploadDocument`, `isUploading`, `getDocuments`) y un "upload-area"
 * con `data-testid` que nunca existió en el componente real -- probaba un
 * mock de sí misma, no el código real. Ver `src/components/DocumentUpload.jsx`
 * y `src/stores/documentStore.js` para la forma real: el componente sube
 * directo a `admin/chatbot/documents/upload` vía `api` (no una acción de
 * store), y el store solo expone `documents/setDocuments/setLoading/setError/
 * setUploadProgress/clearError`.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DocumentUpload from '../../src/components/DocumentUpload';
import { useDocumentStore } from '../../src/stores/documentStore';
import api from '../../src/services/api';

vi.mock('../../src/stores/documentStore', () => ({
    useDocumentStore: vi.fn(),
}));

vi.mock('../../src/services/api', () => ({
    default: {
        get: vi.fn(),
        post: vi.fn(),
        delete: vi.fn(),
    },
}));

function selectFile(container, file) {
    const input = container.querySelector('input[type="file"]');
    return userEvent.upload(input, file);
}

function makeFile(name, sizeBytes, type = 'application/pdf') {
    const file = new File(['contenido'], name, { type });
    Object.defineProperty(file, 'size', { value: sizeBytes });
    return file;
}

describe('DocumentUpload Component', () => {
    const setDocumentsMock = vi.fn();
    const setLoadingMock = vi.fn();
    const setErrorMock = vi.fn();
    const setUploadProgressMock = vi.fn();
    const clearErrorMock = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();

        useDocumentStore.mockReturnValue({
            documents: [],
            loading: false,
            error: null,
            uploadProgress: 0,
            setDocuments: setDocumentsMock,
            setLoading: setLoadingMock,
            setError: setErrorMock,
            setUploadProgress: setUploadProgressMock,
            clearError: clearErrorMock,
        });

        api.get.mockImplementation((url) => {
            if (url === 'admin/chatbot/profiles') return Promise.resolve({ data: [] });
            if (url === 'admin/chatbot/documents') return Promise.resolve({ data: [] });
            return Promise.reject(new Error('URL no mockeada: ' + url));
        });
        api.post.mockResolvedValue({ data: {} });
        api.delete.mockResolvedValue({ data: {} });
    });

    describe('Rendering', () => {
        it('should render the tenant selector, drop area and category selector', () => {
            render(<DocumentUpload />);
            expect(screen.getByText(/proyecto \/ tenant de destino/i)).toBeInTheDocument();
            expect(screen.getByText(/arrastra un archivo aquí/i)).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /seleccionar archivo/i })).toBeInTheDocument();
        });

        it('should render the "Cargar e Indexar en el RAG" button disabled with no file selected', () => {
            render(<DocumentUpload />);
            const uploadButton = screen.getByRole('button', { name: /cargar e indexar en el rag/i });
            expect(uploadButton).toBeDisabled();
        });

        it('should load chatbot profiles and existing documents on mount', async () => {
            render(<DocumentUpload tenantId="centinela-ai" />);
            await waitFor(() => {
                expect(api.get).toHaveBeenCalledWith('admin/chatbot/profiles');
                expect(api.get).toHaveBeenCalledWith('admin/chatbot/documents');
            });
        });
    });

    describe('File selection', () => {
        it('should preview a valid selected file and enable the upload button', async () => {
            const { container } = render(<DocumentUpload />);
            const file = makeFile('reglamento.pdf', 2048);

            await selectFile(container, file);

            expect(screen.getByText('reglamento.pdf')).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /cargar e indexar en el rag/i })).not.toBeDisabled();
        });

        it('should reject a disallowed file extension dropped onto the drop zone', () => {
            // El <input accept="..."> filtra en el picker nativo del navegador
            // (y userEvent.upload lo respeta), pero drag&drop NO respeta `accept` --
            // por eso la validación de extensión del componente es alcanzable de
            // verdad solo simulando un drop, no una selección vía el input.
            const { container } = render(<DocumentUpload />);
            const file = makeFile('virus.exe', 1024, 'application/octet-stream');
            const dropZone = container.querySelector('.border-dashed');

            fireEvent.drop(dropZone, { dataTransfer: { files: [file] } });

            expect(setErrorMock).toHaveBeenCalledWith(expect.stringMatching(/no permitido/i));
            expect(screen.queryByText('virus.exe')).not.toBeInTheDocument();
        });

        it('should reject a file larger than 50MB', async () => {
            const { container } = render(<DocumentUpload />);
            const file = makeFile('enorme.pdf', 60 * 1024 * 1024);

            await selectFile(container, file);

            expect(setErrorMock).toHaveBeenCalledWith(expect.stringMatching(/50 mb/i));
            expect(screen.queryByText('enorme.pdf')).not.toBeInTheDocument();
        });
    });

    describe('Upload flow', () => {
        it('should upload the file with the expected FormData fields and re-fetch documents', async () => {
            const user = userEvent.setup();
            const { container } = render(<DocumentUpload tenantId="centinela-ai" />);

            await waitFor(() => expect(api.get).toHaveBeenCalledWith('admin/chatbot/documents'));
            api.get.mockClear();

            const file = makeFile('manual.pdf', 4096);
            await selectFile(container, file);

            await user.click(screen.getByRole('button', { name: /cargar e indexar en el rag/i }));

            await waitFor(() => {
                expect(api.post).toHaveBeenCalledWith(
                    'admin/chatbot/documents/upload',
                    expect.any(FormData),
                    expect.objectContaining({ headers: { 'Content-Type': 'multipart/form-data' } })
                );
            });

            const formData = api.post.mock.calls[0][1];
            expect(formData.get('title')).toBe('manual.pdf');
            expect(formData.get('category')).toBe('centinela-ai');
            expect(formData.get('doc_type')).toBe('reglamentos');

            // Tras un upload exitoso, se refresca la lista real en vez de simular
            // un documento local (incidente real de duplicación, ver el componente).
            await waitFor(() => {
                expect(api.get).toHaveBeenCalledWith('admin/chatbot/documents');
            });
        });

        it('should report an error via the store if the upload fails', async () => {
            const user = userEvent.setup();
            api.post.mockRejectedValueOnce(new Error('network down'));
            const { container } = render(<DocumentUpload />);

            const file = makeFile('manual.pdf', 4096);
            await selectFile(container, file);
            await user.click(screen.getByRole('button', { name: /cargar e indexar en el rag/i }));

            await waitFor(() => {
                expect(setErrorMock).toHaveBeenCalledWith(expect.stringMatching(/network down/i));
            });
        });
    });

    describe('Documents list', () => {
        it('should render documents from the store with their health status', () => {
            useDocumentStore.mockReturnValue({
                documents: [
                    { id: 'doc-1', name: 'reglamento.pdf', category: 'centinela-ai', chunk_count: 10, embedded_chunk_count: 10, health_pct: 100 },
                ],
                loading: false,
                error: null,
                uploadProgress: 0,
                setDocuments: setDocumentsMock,
                setLoading: setLoadingMock,
                setError: setErrorMock,
                setUploadProgress: setUploadProgressMock,
                clearError: clearErrorMock,
            });

            render(<DocumentUpload />);

            expect(screen.getByText('reglamento.pdf')).toBeInTheDocument();
            expect(screen.getByText('Indexado')).toBeInTheDocument();
            expect(screen.getByText('1 documento(s) disponibles')).toBeInTheDocument();
        });

        it('should show an empty state when there are no documents', () => {
            render(<DocumentUpload />);
            expect(screen.getByText(/no hay documentos registrados/i)).toBeInTheDocument();
        });
    });

    describe('Delete document', () => {
        const oneDocument = {
            documents: [{ id: 'doc-1', name: 'reglamento.pdf', category: 'centinela-ai', chunk_count: 5, embedded_chunk_count: 5, health_pct: 100 }],
            loading: false,
            error: null,
            uploadProgress: 0,
            setDocuments: setDocumentsMock,
            setLoading: setLoadingMock,
            setError: setErrorMock,
            setUploadProgress: setUploadProgressMock,
            clearError: clearErrorMock,
        };

        it('should delete the document after confirmation', async () => {
            const user = userEvent.setup();
            useDocumentStore.mockReturnValue(oneDocument);
            vi.spyOn(window, 'confirm').mockReturnValue(true);

            render(<DocumentUpload />);
            await user.click(screen.getByTitle('Eliminar documento y sus vectores del RAG'));

            await waitFor(() => {
                expect(api.delete).toHaveBeenCalledWith('admin/chatbot/documents/doc-1');
            });
            expect(setDocumentsMock).toHaveBeenCalledWith(expect.any(Function));
        });

        it('should not delete the document if the confirmation is cancelled', async () => {
            const user = userEvent.setup();
            useDocumentStore.mockReturnValue(oneDocument);
            vi.spyOn(window, 'confirm').mockReturnValue(false);

            render(<DocumentUpload />);
            await user.click(screen.getByTitle('Eliminar documento y sus vectores del RAG'));

            expect(api.delete).not.toHaveBeenCalled();
        });
    });
});
