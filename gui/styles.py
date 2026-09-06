"""
Configuração de Estilos da Interface
"""

from tkinter import ttk

def configure_styles():
    """Configura os estilos da interface"""
    style = ttk.Style()
    style.theme_use('clam')
    
    # Cores da paleta
    colors = {
        'primary': '#1B3A5C',
        'secondary': '#2E5A8A',
        'accent': '#4CAF50',
        'danger': '#B00020',
        'warning': '#B5651D',
        'success': '#0F6E56',
        'background': '#F5F7FA',
        'text': '#2D3748',
    }
    
    # Estilos para labels
    style.configure(
        'Title.TLabel',
        font=('Segoe UI', 14, 'bold'),
        foreground=colors['primary']
    )
    
    style.configure(
        'Value.TLabel',
        font=('Segoe UI', 12, 'bold'),
        foreground=colors['text']
    )
    
    style.configure(
        'Warning.TLabel',
        foreground=colors['warning']
    )
    
    style.configure(
        'Danger.TLabel',
        foreground=colors['danger']
    )
    
    style.configure(
        'Success.TLabel',
        foreground=colors['success']
    )
    
    # Estilos para botões
    style.configure(
        'Accent.TButton',
        background=colors['accent'],
        foreground='white',
        font=('Segoe UI', 10, 'bold')
    )
    
    style.map(
        'Accent.TButton',
        background=[('active', '#45a049')]
    )
    
    # Estilos para frames
    style.configure(
        'Card.TFrame',
        relief='ridge',
        borderwidth=1,
        background='white'
    )