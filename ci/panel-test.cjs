// Ejecuta los layouts completos con la API de Plasma simulada: no modifica una sesión real.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const result = [];

class Widget {
    constructor(type) { this.type = type; this.currentConfigGroup = []; this.config = {}; this.writes = 0; }
    key(key) { return [...this.currentConfigGroup, key].join('/'); }
    writeConfig(key, value) { this.config[this.key(key)] = value; this.writes++; }
    readConfig(key, fallback) { return this.config[this.key(key)] ?? fallback; }
}
function general(widget) { return Object.fromEntries(Object.entries(widget.config).filter(([k]) => k.startsWith('General/')).map(([k,v]) => [k.slice(8),v])); }

for (const layout of ['org.antuos.desktop', 'org.antuos.mac']) {
    for (const live of [false, true]) {
        for (const grid of [18, 24, 36]) {
            for (const legacy of [false, true]) {
                const bars = [], desktops = [{}];
                const inner = new Widget('org.kde.plasma.private.systemtray');
                class Panel {
                    constructor() { this.items = []; bars.push(this); }
                    addWidget(type) {
                        const widget = new Widget(type);
                        if (legacy && type === 'org.kde.plasma.systemtray') widget.config.SystrayContainmentId = 123;
                        this.items.push(widget); return widget;
                    }
                }
                const context = vm.createContext({Panel, gridUnit:grid,
                    applicationExists: name => name === 'antu-instalador.desktop' ? live : name === 'com.brave.Browser.desktop' ? !live : true,
                    currentActivity: () => 'test', desktopsForActivity: () => desktops,
                    desktopById: id => { assert.equal(id,123); return inner; }
                });
                const file = `files/system/usr/share/plasma/look-and-feel/${layout}/contents/layouts/org.kde.plasma.desktop-layout.js`;
                vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'), context, {filename:file});
                assert.equal(bars.length, layout.endsWith('.desktop') ? 1 : 2);
                const bottom = bars.find(b => b.location === 'bottom');
                assert(bottom.floating);
                assert.equal(bottom.height, Math.max(56,2*Math.ceil(grid*3/2)));
                const task = bottom.items.find(w => w.type === 'org.kde.plasma.icontasks');
                const config = general(task);
                assert.equal(config.launchers.length, live ? 6 : 5);
                assert.equal(new Set(config.launchers).size, config.launchers.length);
                for (const removed of ['zenit.desktop','systemsettings.desktop','org.kde.discover.desktop'])
                    assert(!config.launchers.some(s => s.endsWith(removed)));
                assert(config.launchers.includes('preferred://filemanager'));
                assert(config.launchers.includes('applications:steam.desktop'));
                assert.equal(config.launchers[0],live ? 'applications:antu-bienvenida.desktop' : 'applications:com.brave.Browser.desktop');
                assert.equal(config.fill,false); assert.equal(config.iconSpacing,2); assert.equal(config.maxStripes,1);
                assert.equal(config.hideLauncherOnStart,true); assert.equal(config.separateLaunchers,false);
                const bar = bars.find(b => b.items.some(w => w.type === 'org.kde.plasma.systemtray'));
                const trayIndex = bar.items.findIndex(w => w.type === 'org.kde.plasma.systemtray');
                const tray = legacy ? inner : bar.items[trayIndex];
                assert.equal(general(tray).showAllItems,false);
                assert.equal(general(tray).scaleIconsToFit,false);
                assert.deepEqual(Array.from(general(tray).hiddenItems),['org.kde.plasma.clipboard','org.kde.plasma.mediacontroller']);
                assert.equal(general(bar.items[trayIndex+1]).length,12);
                assert.equal(general(bar.items[trayIndex+1]).expanding,false);
                const clock = bar.items.find(w => w.type === 'org.kde.plasma.digitalclock');
                assert(clock.config['Appearance/fontSize'] >= 12);
                assert.equal(desktops[0].wallpaperPlugin,'org.kde.image');
                result.push({layout,live,grid,legacy,height:bottom.height,launchers:Array.from(config.launchers)});
            }
        }
    }
}

// La migración retira solo Zenit, respeta el resto y es idempotente.
const migration = fs.readFileSync(path.join(root,'files/system/usr/share/plasma/shells/org.kde.plasma.desktop/contents/updates/antu-2026-11-zenit-tray.js'),'utf8');
for (const theme of ['org.antuos.desktop','org.antuos.mac','org.kde.breeze.desktop']) {
    for (const stringList of [false,true]) {
        const widget = new Widget('org.kde.plasma.icontasks');
        const before = ['applications:mi-app.desktop','applications:zenit.desktop','applications:steam.desktop'];
        widget.config['General/launchers'] = stringList ? before.join(',') : before;
        const context = vm.createContext({ConfigFile:()=>({readEntry:()=>theme}),panels:()=>[{widgets:()=>[widget]}]});
        vm.runInContext(migration,context);
        if (theme.startsWith('org.antuos.')) {
            assert.deepEqual(Array.from(widget.config['General/launchers']),[before[0],before[2]]);
            const writes = widget.writes; vm.runInContext(migration,context); assert.equal(widget.writes,writes);
        } else { assert.equal(widget.writes,0); }
    }
}
if (process.argv.includes('--json')) process.stdout.write(JSON.stringify({layoutCases:result,migrationCases:6},null,2)+'\n');
else console.log(`Panel: ${result.length} combinaciones de layout y 6 migraciones correctas; sin Zenit fijado ni accesos duplicados.`);
