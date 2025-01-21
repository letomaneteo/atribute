        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 0, 1);

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.outputEncoding = THREE.sRGBEncoding;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.5;
        document.body.appendChild(renderer.domElement);

        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(5, 10, 7.5).normalize();
        scene.add(directionalLight);

        new THREE.EXRLoader()
            .load('https://raw.githubusercontent.com/letomaneteo/21/main/sunset_fairway_4k.exr', (texture) => {
                texture.mapping = THREE.EquirectangularReflectionMapping;
                scene.environment = texture;
            });

        const loader = new THREE.GLTFLoader();
        let model;
        let mixer;
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();

        const targetObjects = [
            { name: "Mesh002", animationName: "Object03Action" },
            { name: "Mesh005", animationName: "Object01Action" },
            { name: "Mesh014", animationName: "Object02Action" },
        ];

        const interactiveObjects = [];

        loader.load(
            'https://raw.githubusercontent.com/letomaneteo/21/main/3tumbalux.glb',
            (gltf) => {
                model = gltf.scene;
                mixer = new THREE.AnimationMixer(model);

                model.traverse((child) => {
                    if (child.isMesh) {
                        child.material.envMap = scene.environment;
                        child.material.needsUpdate = true;

                        const target = targetObjects.find(obj => obj.name === child.name);
                        if (target) {
                            const animationClip = gltf.animations.find(anim => anim.name === target.animationName);
                            if (animationClip) {
                                const action = mixer.clipAction(animationClip);
                                action.clampWhenFinished = true;
                                action.loop = THREE.LoopOnce;
                                interactiveObjects.push({ mesh: child, action, playingForward: true });
                            }
                        }
                    }
                });
model.rotation.set(0, Math.PI / 2, 0);
                scene.add(model);
            },
            undefined,
            (error) => console.error('Ошибка загрузки модели:', error)
        );

        function onPointerClick(event) {
            mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

            raycaster.setFromCamera(mouse, camera);

            const intersects = raycaster.intersectObjects(interactiveObjects.map(obj => obj.mesh), true);

            if (intersects.length > 0) {
                const clickedMesh = intersects[0].object;

                interactiveObjects.forEach((obj) => {
                    if (obj.mesh === clickedMesh) {
                        if (obj.playingForward) {
                            obj.action.reset();
                            obj.action.timeScale = 1;
                            obj.action.play();
                        } else {
                            obj.action.reset();
                            obj.action.timeScale = -1;
                            obj.action.time = obj.action.getClip().duration;
                            obj.action.play();
                        }
                        obj.playingForward = !obj.playingForward;
                    }
                });
            }
        }

        window.addEventListener('click', onPointerClick);

        let isDragging = false;
        let previousMousePosition = { x: 0, y: 0 };
        let autoRotate = true;
        const rotationSpeed = 0.001;
        let touchStartPosition = { x: 0, y: 0 };
        let touchStartDistance = 0;

        // Блокировка прокрутки при вращении
        let isRotationActive = false;

        renderer.domElement.addEventListener('mousedown', (event) => {
            isDragging = true;
            autoRotate = false;
            previousMousePosition = { x: event.clientX, y: event.clientY };
            isRotationActive = true; // Включаем блокировку прокрутки при вращении
        });

        renderer.domElement.addEventListener('mousemove', (event) => {
            if (isDragging && model) {
                const deltaMove = {
                    x: event.clientX - previousMousePosition.x,
                    y: event.clientY - previousMousePosition.y,
                };

                model.rotation.y += deltaMove.x * 0.005;
                model.rotation.x += deltaMove.y * 0.005;

                previousMousePosition = { x: event.clientX, y: event.clientY };
            }
        });

        renderer.domElement.addEventListener('mouseup', () => {
            isDragging = false;
            autoRotate = true;
            isRotationActive = false; // Отключаем блокировку прокрутки после вращения
        });

        renderer.domElement.addEventListener('wheel', (event) => {
            if (isRotationActive) {
                event.preventDefault(); // Отключаем прокрутку страницы при вращении
            }
            if (model) {
                const scaleChange = event.deltaY > 0 ? 0.95 : 1.05;
                model.scale.multiplyScalar(scaleChange);
            }
        });

        // Блокировка прокрутки только во время взаимодействия с канвасом
renderer.domElement.addEventListener('touchstart', (event) => {
    if (event.touches.length === 1) {
        touchStartPosition = { x: event.touches[0].clientX, y: event.touches[0].clientY };
    } else if (event.touches.length === 2) {
        event.preventDefault(); // Блокировка прокрутки страницы при масштабировании
        const dx = event.touches[0].clientX - event.touches[1].clientX;
        const dy = event.touches[0].clientY - event.touches[1].clientY;
        touchStartDistance = Math.sqrt(dx * dx + dy * dy);
    }
});

renderer.domElement.addEventListener('touchmove', (event) => {
    if (event.touches.length === 1 && model) {
        const touchCurrentPosition = { x: event.touches[0].clientX, y: event.touches[0].clientY };
        const deltaMove = {
            x: touchCurrentPosition.x - touchStartPosition.x,
            y: touchCurrentPosition.y - touchStartPosition.y,
        };

        model.rotation.y += deltaMove.x * 0.005;
        model.rotation.x += deltaMove.y * 0.005;

        touchStartPosition = touchCurrentPosition;

        event.preventDefault(); // Блокировка прокрутки страницы при вращении модели
    } else if (event.touches.length === 2 && model) {
        event.preventDefault(); // Блокировка прокрутки страницы при масштабировании
        const dx = event.touches[0].clientX - event.touches[1].clientX;
        const dy = event.touches[0].clientY - event.touches[1].clientY;
        const distance = Math.sqrt(dx * dx + dy * dy);

        const scaleChange = distance / touchStartDistance;
        model.scale.multiplyScalar(scaleChange);
        touchStartDistance = distance;
    }
});

// Оригинальный код для обработки скролла на ПК остается без изменений
renderer.domElement.addEventListener('wheel', (event) => {
    event.preventDefault(); // Отключение прокрутки страницы на ПК
    if (model) {
        const scaleChange = event.deltaY > 0 ? 0.95 : 1.05;
        model.scale.multiplyScalar(scaleChange);
    }
});

        const clock = new THREE.Clock();
        function animate() {
            requestAnimationFrame(animate);

            const delta = clock.getDelta();
            if (mixer) mixer.update(delta);

            if (autoRotate && model) {
                model.rotation.y += rotationSpeed;
            }

            renderer.render(scene, camera);
        }

        animate();

        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
