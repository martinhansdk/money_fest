/**
 * Toast notification system with Tailwind CSS styling
 */

class ToastManager {
    constructor() {
        this.container = null;
        this.toasts = [];
        this.init();
    }

    init() {
        // Create toast container
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        this.container.className = 'fixed top-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none';
        this.container.setAttribute('role', 'status');
        this.container.setAttribute('aria-live', 'polite');
        document.body.appendChild(this.container);
    }

    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `
            pointer-events-auto
            flex items-center gap-3 min-w-[280px] max-w-[380px]
            px-4 py-3 rounded-lg shadow-lg
            transform translate-x-full opacity-0
            transition-all duration-300 ease-out
            ${this.getTypeClasses(type)}
        `.replace(/\s+/g, ' ').trim();

        const icon = this.getIcon(type);
        toast.innerHTML = `
            <span class="text-lg flex-shrink-0">${icon}</span>
            <span class="flex-1 text-sm font-medium">${this.escapeHtml(message)}</span>
            <button class="text-current opacity-60 hover:opacity-100 text-lg leading-none p-1 -mr-1">×</button>
        `;

        // Close button handler
        toast.querySelector('button').addEventListener('click', () => {
            this.dismiss(toast);
        });

        this.container.appendChild(toast);
        this.toasts.push(toast);

        // Trigger animation
        requestAnimationFrame(() => {
            toast.classList.remove('translate-x-full', 'opacity-0');
            toast.classList.add('translate-x-0', 'opacity-100');
        });

        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => this.dismiss(toast), duration);
        }

        return toast;
    }

    getTypeClasses(type) {
        switch (type) {
            case 'success':
                return 'bg-green-500 text-white';
            case 'error':
                return 'bg-red-500 text-white';
            case 'warning':
                return 'bg-yellow-500 text-white';
            case 'info':
            default:
                return 'bg-gray-700 text-white';
        }
    }

    getIcon(type) {
        switch (type) {
            case 'success':
                return '✓';
            case 'error':
                return '✕';
            case 'warning':
                return '⚠';
            case 'info':
            default:
                return 'ℹ';
        }
    }

    dismiss(toast) {
        if (!toast || !toast.parentElement) return;

        toast.classList.remove('translate-x-0', 'opacity-100');
        toast.classList.add('translate-x-full', 'opacity-0');

        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
            const index = this.toasts.indexOf(toast);
            if (index > -1) {
                this.toasts.splice(index, 1);
            }
        }, 300);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    success(message, duration) {
        return this.show(message, 'success', duration);
    }

    error(message, duration) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration) {
        return this.show(message, 'info', duration);
    }
}

// Create global instance
const toast = new ToastManager();

// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Format amount utility (returns plain text with sign)
function formatAmount(amount) {
    const num = parseFloat(amount);
    const sign = num >= 0 ? '+' : '';
    return sign + num.toFixed(2);
}
