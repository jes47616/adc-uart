// ringbuffer.c
#include "ringbuffer.h"

void ring_buffer_init(ring_buffer_t *buffer, char *buf, ring_buffer_size_t size) {
    buffer->buffer = buf;
    buffer->size = size;
    buffer->head = 0;
    buffer->tail = 0;
    buffer->count = 0;
}

ring_buffer_size_t ring_buffer_queue_arr(ring_buffer_t *buffer, const char *data, ring_buffer_size_t size) {
    if (buffer->count + size > buffer->size) {
        return 0; // Not enough space
    }

    for (ring_buffer_size_t i = 0; i < size; i++) {
        buffer->buffer[buffer->head] = data[i];
        buffer->head = (buffer->head + 1) % buffer->size;
    }
    buffer->count += size;
    return size;
}

ring_buffer_size_t ring_buffer_dequeue_arr(ring_buffer_t *buffer, char *data, ring_buffer_size_t size) {
    ring_buffer_size_t bytes_to_read = (size > buffer->count) ? buffer->count : size;
    
    for (ring_buffer_size_t i = 0; i < bytes_to_read; i++) {
        data[i] = buffer->buffer[buffer->tail];
        buffer->tail = (buffer->tail + 1) % buffer->size;
    }
    buffer->count -= bytes_to_read;
    return bytes_to_read;
}

uint8_t ring_buffer_is_empty(ring_buffer_t *buffer) {
    return (buffer->count == 0);
}

uint8_t ring_buffer_is_full(ring_buffer_t *buffer) {
    return (buffer->count == buffer->size);
}

ring_buffer_size_t ring_buffer_num_items(ring_buffer_t *buffer) {
    return buffer->count;
}