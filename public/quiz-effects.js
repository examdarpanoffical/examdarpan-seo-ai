(function(){
  if(location.pathname.replace(/\/+$/,'')!=='/quiz') return;

  const style=document.createElement('style');
  style.textContent=`
    .ed-celebration-layer{
      position:fixed;
      inset:0;
      pointer-events:none;
      overflow:hidden;
      z-index:9999;
    }

    .ed-confetti{
      position:absolute;
      top:-22px;
      width:8px;
      height:14px;
      border-radius:3px;
      opacity:0;
      will-change:transform,opacity;
      animation:edConfettiFall var(--dur) cubic-bezier(.18,.72,.25,1) var(--delay) forwards;
    }

    .ed-confetti.round{
      border-radius:50%;
      width:8px;
      height:8px;
    }

    .ed-confetti.ribbon{
      width:5px;
      height:20px;
      border-radius:999px;
    }

    @keyframes edConfettiFall{
      0%{
        opacity:0;
        transform:translate3d(0,-24px,0) rotate(0deg) scale(.65);
      }
      7%{opacity:1}
      38%{
        opacity:1;
        transform:translate3d(var(--x1),38vh,0) rotate(var(--r1)) scale(1);
      }
      72%{
        opacity:.98;
        transform:translate3d(var(--x2),74vh,0) rotate(var(--r2)) scale(.95);
      }
      100%{
        opacity:0;
        transform:translate3d(var(--x3),112vh,0) rotate(var(--r3)) scale(.78);
      }
    }

    .ed-success-spark{
      position:fixed;
      left:50%;
      top:42%;
      width:10px;
      height:10px;
      border-radius:50%;
      pointer-events:none;
      z-index:10000;
      opacity:0;
      animation:edSpark .9s ease-out forwards;
    }

    @keyframes edSpark{
      0%{
        opacity:0;
        transform:translate(-50%,-50%) scale(.3);
      }
      18%{opacity:1}
      100%{
        opacity:0;
        transform:
          translate(
            calc(-50% + var(--sx)),
            calc(-50% + var(--sy))
          )
          scale(1.8);
      }
    }

    @media(prefers-reduced-motion:reduce){
      .ed-confetti,
      .ed-success-spark{
        animation:none!important;
        display:none!important;
      }
    }
  `;

  document.head.appendChild(style);

  let celebrated=false;

  function celebrate(){
    if(celebrated) return;
    celebrated=true;

    if(window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const layer=document.createElement('div');
    layer.className='ed-celebration-layer';

    const mobile=window.innerWidth<600;
    const count=mobile?82:135;

    const colors=[
      '#22c55e',
      '#3b82f6',
      '#f59e0b',
      '#ef4444',
      '#8b5cf6',
      '#ec4899',
      '#06b6d4',
      '#ffffff'
    ];

    for(let i=0;i<count;i++){
      const piece=document.createElement('span');
      const kind=i%3;

      piece.className=
        'ed-confetti'+
        (kind===1?' round':kind===2?' ribbon':'');

      piece.style.left=`${Math.random()*100}%`;
      piece.style.background=colors[i%colors.length];

      piece.style.setProperty(
        '--dur',
        `${2.4+Math.random()*1.7}s`
      );

      piece.style.setProperty(
        '--delay',
        `${Math.random()*.28}s`
      );

      piece.style.setProperty(
        '--x1',
        `${-100+Math.random()*200}px`
      );

      piece.style.setProperty(
        '--x2',
        `${-150+Math.random()*300}px`
      );

      piece.style.setProperty(
        '--x3',
        `${-220+Math.random()*440}px`
      );

      piece.style.setProperty(
        '--r1',
        `${-360+Math.random()*720}deg`
      );

      piece.style.setProperty(
        '--r2',
        `${-720+Math.random()*1440}deg`
      );

      piece.style.setProperty(
        '--r3',
        `${-1080+Math.random()*2160}deg`
      );

      layer.appendChild(piece);
    }

    document.body.appendChild(layer);

    for(let i=0;i<16;i++){
      const spark=document.createElement('span');

      spark.className='ed-success-spark';
      spark.style.background=colors[i%colors.length];

      spark.style.setProperty(
        '--sx',
        `${Math.cos(i*Math.PI/8)*90}px`
      );

      spark.style.setProperty(
        '--sy',
        `${Math.sin(i*Math.PI/8)*70}px`
      );

      spark.style.animationDelay=`${i*8}ms`;

      document.body.appendChild(spark);

      setTimeout(
        ()=>spark.remove(),
        1100+i*8
      );
    }

    setTimeout(
      ()=>layer.remove(),
      4800
    );
  }

  function watch(){
    const box=document.getElementById('quizResult');

    if(!box){
      setTimeout(watch,250);
      return;
    }

    let wasVisible=
      !box.hidden &&
      !!box.innerHTML.trim();

    const observer=new MutationObserver(()=>{
      const visible=
        !box.hidden &&
        !!box.innerHTML.trim();

      if(visible && !wasVisible){
        celebrate();
      }

      wasVisible=visible;
    });

    observer.observe(box,{
      attributes:true,
      attributeFilter:['hidden'],
      childList:true,
      subtree:true
    });
  }

  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',watch);
  }else{
    watch();
  }
})();
