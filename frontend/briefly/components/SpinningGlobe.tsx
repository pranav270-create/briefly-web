'use client';

import { useEffect, useRef } from 'react';
import * as THREE from 'three';

const SpinningGlobe = () => {
  const outputRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function init() {
        const WIDTH = 48;
        const HEIGHT = 48;
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(1, WIDTH / HEIGHT, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({
          alpha: true,
          antialias: true
        });
        scene.background = new THREE.Color( 0x808080 );
        renderer.setSize(WIDTH, HEIGHT);
        // renderer.domElement.style.display = 'block';
        // document.body.appendChild(renderer.domElement);
        
        const texture = new THREE.TextureLoader().load('https://threejsfundamentals.org/threejs/resources/images/world.jpg');

        const geometry = new THREE.SphereGeometry( 3, 64, 48 );
        const material = new THREE.MeshStandardMaterial( {
            color: 0xffffff,
            emissive: 0x000000,
            roughness: 1,
            metalness: 1,
            map: texture
        } );

        const globe = new THREE.Mesh( geometry, material );
        globe.rotation.z = Math.PI;
        globe.rotation.y = 1.5;
        scene.add( globe );
        
        const light = new THREE.PointLight( 0xffffff, 3.33, 0 );
        light.position.set( 150, -150, 1500 );
        scene.add( light );
        
        const light2 = new THREE.PointLight(0xffffff, 2, 0);
        light2.position.set(-125, 100, -500);
        scene.add(light2);
        
        camera.position.z = 345;
        document.body.appendChild(renderer.domElement);
        const gl = renderer.getContext();

        // Add this line to preserve the drawing buffer
        renderer.preserveDrawingBuffer = true;
        console.log('Renderer size:', renderer.getSize(new THREE.Vector2()));

        const pixels = new Uint8Array(gl.drawingBufferWidth * gl.drawingBufferHeight * 4);
        console.log('Pixel buffer created, size:', pixels.length);

    
        const ASCII = "   ·—+=##";
      
        function render() {
            requestAnimationFrame(render);
            globe.rotation.y -= 0.01;
            renderer.render(scene, camera);
    
            setTimeout(() => {
                const canvas = renderer.domElement;
                console.log('Canvas size:', canvas.width, canvas.height);
                console.log('Renderer size:', renderer.getSize(new THREE.Vector2()));
            
                gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
                console.log('Pixels read, first few values:', pixels.slice(0, 10));
            
                const grayscalePixels = grayscale10(pixels);
                console.log('Grayscale pixels, first few values:', grayscalePixels.slice(0, 10));
            
                let text = grayscalePixels.map(asciify).join("");
                text = text.split("\n").map(reverseString).join("\n");
                if (outputRef.current) {
                  outputRef.current.innerHTML = text;
                  console.log('ASCII art updated');
                } else {
                  console.warn('outputRef.current is null');
                }
              }, 100);
            }

        function reverseString(str: string) {
            return str.split("").reverse().join("");
        }
      
        function grayscale10(pixels: Uint8Array) {
            const length = pixels.length;
            const gsPixels = [];
            for (let i = 0; i < length; i += 4) {
              gsPixels.push(
                Math.floor(
                  (pixels[i] + pixels[i+1] + pixels[i+2]) /
                  768 * ASCII.length
                )
              );
            }
            return gsPixels;
        }
          
        function asciify(val: number, index: number) {
            const br = index !== 0 && index % WIDTH === 0 ? "\n" : "";
            return br + ASCII[val];
        }

      render();
    }
      
    // Call the init function immediately
    init();

    // Cleanup function
    return () => {
        if (outputRef.current) {
          outputRef.current.innerHTML = '';
        }
      };
    }, []);
  
return (
    <div className="spinning-globe">
        <div id="output" ref={outputRef}></div>
    </div>
    );
};

export default SpinningGlobe;