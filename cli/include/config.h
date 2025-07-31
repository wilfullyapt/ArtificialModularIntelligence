#ifndef CONFIG_H
#define CONFIG_H

extern char *api_key;
extern char *api_endpoint;

void init_config(void);
void cleanup_config(void);

#endif
