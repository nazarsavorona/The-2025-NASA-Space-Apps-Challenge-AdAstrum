# 💡 Виправлення освітлення в режимах Single Planet і Star System

## Проблема
Планета була темною в режимі "Single Planet" (без зірки), але освітлена в режимі "Star System".

## Рішення

### 1. **Покращене базове освітлення**
```javascript
// Збільшено інтенсивність ambient light з 0.5 до 0.6
const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);

// Змінено з PointLight на DirectionalLight для кращого покриття
dynamicLight = new THREE.DirectionalLight(0xffffff, 1.5);
```

### 2. **Динамічне позиціонування світла**

#### Режим Single Planet:
```javascript
// Світло розташовується перед планетою
dynamicLight.position.set(3, 3, 5);
dynamicLight.color.setHex(0xffffff);
dynamicLight.intensity = 2;
```

#### Режим Star System:
```javascript
// Світло випромінюється від зірки
dynamicLight.position.set(0, 2, 0);
dynamicLight.color.setHex(starColor); // Колір зірки
dynamicLight.intensity = 2;

// Плюс точкове світло від зірки
const starLight = new THREE.PointLight(starColor, 3, 100);
starLight.position.set(0, 0, 0);
```

### 3. **Покращені матеріали планет**
```javascript
let planetMaterial = new THREE.MeshStandardMaterial({ 
    color: 0x4488ff,
    roughness: 0.7,  // Матова поверхня
    metalness: 0.1   // Трохи відблиску
});
```

## Результат

✅ **Single Planet режим**: Планета тепер яскраво освітлена, добре видно деталі текстури  
✅ **Star System режим**: Реалістичне освітлення від зірки з її кольором  
✅ **Плавне перемикання**: Світло автоматично адаптується при зміні режиму

## Типи світла в Three.js

1. **AmbientLight** - загальне фонове освітлення (без тіней)
2. **DirectionalLight** - спрямоване світло (як сонце, паралельні промені)
3. **PointLight** - точкове світло (світить у всі боки від точки)

## Додаткові переваги

- **Кращий контраст**: Roughness і metalness роблять поверхню більш реалістичною
- **Економія ресурсів**: Один динамічний DirectionalLight замість багатьох джерел
- **Правильна фізика**: Колір світла від зірки відповідає її температурі

## Як перевірити

1. Перезавантажте сторінку: http://localhost:3000
2. Виберіть будь-яку планету
3. Перемкніться між "Single Planet" і "Star System"
4. Планета повинна бути добре освітлена в обох режимах!

---

**Технічні деталі**:
- DirectionalLight працює як сонце - паралельні промені
- PointLight працює як лампочка - світить у всі боки
- AmbientLight додає загальну яскравість, щоб не було повної темряви
