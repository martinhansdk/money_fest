/**
 * WebSocket client for real-time batch updates
 * Handles connection, auto-reconnect, and event dispatching
 */

class BatchWebSocket {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000; // Start with 1 second
        this.subscribedBatchId = null;
        this.pingInterval = null;
        this.eventHandlers = {};
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        // Determine WebSocket URL based on current location
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const wsUrl = `${protocol}//${host}/ws`;

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.reconnectDelay = 1000;

                // Resubscribe to batch if we were subscribed before
                if (this.subscribedBatchId) {
                    this.subscribe(this.subscribedBatchId);
                }

                // Start ping interval to keep connection alive
                this.startPing();

                // Dispatch connected event
                this.dispatch('connected');
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.stopPing();
                this.dispatch('disconnected');
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.dispatch('error', error);
            };

        } catch (error) {
            console.error('Error creating WebSocket:', error);
            this.attemptReconnect();
        }
    }

    /**
     * Attempt to reconnect with exponential backoff
     */
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.dispatch('max_reconnect_attempts');
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);

        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        setTimeout(() => {
            this.connect();
        }, delay);
    }

    /**
     * Start sending ping messages to keep connection alive
     */
    startPing() {
        this.stopPing();
        this.pingInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.send({ type: 'ping' });
            }
        }, 30000); // Ping every 30 seconds
    }

    /**
     * Stop ping interval
     */
    stopPing() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    /**
     * Send a message to the server
     */
    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected, cannot send message');
        }
    }

    /**
     * Subscribe to batch updates
     */
    subscribe(batchId) {
        this.subscribedBatchId = batchId;
        this.send({ type: 'subscribe', batch_id: batchId });
    }

    /**
     * Unsubscribe from batch updates
     */
    unsubscribe(batchId) {
        this.send({ type: 'unsubscribe', batch_id: batchId });
        if (this.subscribedBatchId === batchId) {
            this.subscribedBatchId = null;
        }
    }

    /**
     * Handle incoming message from server
     */
    handleMessage(message) {
        const { type } = message;

        switch (type) {
            case 'subscribed':
                console.log(`Subscribed to batch ${message.batch_id}`);
                this.dispatch('subscribed', message);
                break;

            case 'unsubscribed':
                console.log(`Unsubscribed from batch ${message.batch_id}`);
                this.dispatch('unsubscribed', message);
                break;

            case 'transaction_updated':
                console.log('Transaction updated:', message.transaction);
                this.dispatch('transaction_updated', message);
                break;

            case 'batch_progress':
                console.log('Batch progress:', message.progress);
                this.dispatch('batch_progress', message);
                break;

            case 'batch_complete':
                console.log('Batch complete!', message.batch_id);
                this.dispatch('batch_complete', message);
                break;

            case 'pong':
                // Pong received, connection is alive
                break;

            default:
                console.warn('Unknown message type:', type);
        }
    }

    /**
     * Register an event handler
     */
    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }

    /**
     * Unregister an event handler
     */
    off(event, handler) {
        if (!this.eventHandlers[event]) return;
        this.eventHandlers[event] = this.eventHandlers[event].filter(h => h !== handler);
    }

    /**
     * Dispatch an event to registered handlers
     */
    dispatch(event, data) {
        if (!this.eventHandlers[event]) return;
        this.eventHandlers[event].forEach(handler => {
            try {
                handler(data);
            } catch (error) {
                console.error(`Error in ${event} handler:`, error);
            }
        });
    }

    /**
     * Close the WebSocket connection
     */
    close() {
        this.stopPing();
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.subscribedBatchId = null;
    }
}

// Create global instance
const batchWS = new BatchWebSocket();
