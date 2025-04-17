// ringbuffer.h
#ifndef RINGBUFFER_H
#define RINGBUFFER_H

#include <inttypes.h>
#include <stddef.h>
#include <assert.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef size_t ring_buffer_size_t;

typedef struct ring_buffer_t {
    char *buffer;
    ring_buffer_size_t size;
    ring_buffer_size_t head;
    ring_buffer_size_t tail;
    ring_buffer_size_t count;
} ring_buffer_t;

void ring_buffer_init(ring_buffer_t *buffer, char *buf, ring_buffer_size_t size);
ring_buffer_size_t ring_buffer_queue_arr(ring_buffer_t *buffer, const char *data, ring_buffer_size_t size);
ring_buffer_size_t ring_buffer_dequeue_arr(ring_buffer_t *buffer, char *data, ring_buffer_size_t size);
uint8_t ring_buffer_is_empty(ring_buffer_t *buffer);
uint8_t ring_buffer_is_full(ring_buffer_t *buffer);
ring_buffer_size_t ring_buffer_num_items(ring_buffer_t *buffer);

#ifdef __cplusplus
}
#endif

#endif /* RINGBUFFER_H */