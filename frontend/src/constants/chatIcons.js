// Biblioteca de íconos seleccionables para el widget/chat, compartida entre el
// selector del panel admin (AdminPage.jsx) y el render real del chat
// (ChatInterface.jsx). Antes vivía duplicada solo en AdminPage.jsx -- el chat
// real nunca la usaba y siempre mostraba el 🤖 genérico sin importar el ícono
// elegido en el admin (incidente real 2026-08-14). Un solo lugar evita que
// ambos se desincronicen otra vez.
import {
    Bot, Sparkles, MessageSquare, HelpCircle, ShieldCheck, Scale, FileText,
    Building2, User, Cpu, Headphones, Zap,
} from 'lucide-react'

export const ICON_MAP = {
    Bot, Sparkles, MessageSquare, HelpCircle, ShieldCheck, Scale, FileText, Building2, User, Cpu, Headphones, Zap
}

export const ICON_LIBRARY = [
    { id: 'Bot', label: 'Bot', Icon: Bot },
    { id: 'Sparkles', label: 'IA Destellos', Icon: Sparkles },
    { id: 'MessageSquare', label: 'Chat', Icon: MessageSquare },
    { id: 'HelpCircle', label: 'Ayuda', Icon: HelpCircle },
    { id: 'ShieldCheck', label: 'Seguridad', Icon: ShieldCheck },
    { id: 'Scale', label: 'Legal / RPP', Icon: Scale },
    { id: 'FileText', label: 'Documentos', Icon: FileText },
    { id: 'Building2', label: 'Catastro / IRCEP', Icon: Building2 },
    { id: 'User', label: 'Asistente', Icon: User },
    { id: 'Cpu', label: 'Algoritmo', Icon: Cpu },
    { id: 'Headphones', label: 'Soporte', Icon: Headphones },
    { id: 'Zap', label: 'Rápido', Icon: Zap },
]
