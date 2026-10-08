import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./e2e',use:{baseURL:'http://127.0.0.1:5173',launchOptions:{args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']}},webServer:{command:'npx vite --host 127.0.0.1',url:'http://127.0.0.1:5173',reuseExistingServer:!process.env.CI},projects:[{name:'chromium',use:{browserName:'chromium'}}]});
