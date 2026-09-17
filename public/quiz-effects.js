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
      top:-18px;
      width:8px;
      height:14px;
      border-radius:2px;
      opacity:0;
      animation:edConfettiFall var(--dur) cubic-bezier(.18,.72,.25,1) var(--delay) forwards;
    }

    .ed-confetti.round{
      border-radius:50%;
      width:7px;
      height:7px;
    }

    .ed-confetti.ribbon{
      width:5px;
      height:18px;
      border-radius:999px;
    }

    @keyframes edConfettiFall{
      0%{
        opacity:0;
        transform:translate3d(0,-20px,0) rotate(0deg) scale(.7);
      }
      8%{opacity:1}
      42%{
        opacity:1;
        transform:translate3d(var(--x1),42vh,0) rotate(var(--r1)) scale(1);
      }
      78%{opacity:.95}
      100%{
        opacity:0;
        transform:translate3d(var(--x2),112vh,0) rotate(var(--r2)) scale(.85);
      }
    }

    .ed-result-pop{
      animation:edResultPop .5s cubic-bezier(.2,.85,.25,1.15);
    }

    @keyframes edResultPop{
      0%{
        opacity:.35;
        transform:scale(.985);
      }
      65%{
        opacity:1;
        transform:scale(1.012);
      }
      100%{
        opacity:1;
        transform:none;
      }
    }

    @media(prefers-reduced-motion:reduce){
      .ed-confetti{
        animation:none!important;
        display:none;
      }
      .ed-result-pop{
        animation:none!important;
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

    const count=window.innerWidth<600 ? 70 : 110;

    const colors=[
      '#22c55e',
      '#3b82f6',
      '#f59e0b',
      '#ef4444',
      '#8b5cf6',
      '#ec4899',
      '#06b6d4'
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
        `${2.5+Math.random()*1.8}s`
      );

      piece.style.setProperty(
        '--delay',
        `${Math.random()*.45}s`
      );

      piece.style.setProperty(
        '--x1',
        `${-80+Math.random()*160}px`
      );

      piece.style.setProperty(
        '--x2',
        `${-160+Math.random()*320}px`
      );

      piece.style.setProperty(
        '--r1',
        `${-360+Math.random()*720}deg`
      );

      piece.style.setProperty(
        '--r2',
        `${-900+Math.random()*1800}deg`
      );

      layer.appendChild(piece);
    }

    document.body.appendChild(layer);

    setTimeout(()=>{
      layer.remove();
    },5200);
  }

  function showResult(){
    const box=document.getElementById('quizResult');

    if(!box || box.hidden || !box.innerHTML.trim()) return;

    celebrate();

    box.classList.remove('ed-result-pop');
    void box.offsetWidth;
    box.classList.add('ed-result-pop');
  }

  function watch(){
    const box=document.getElementById('quizResult');

    if(!box){
      setTimeout(watch,250);
      return;
    }

    const observer=new MutationObserver(()=>{
      if(!box.hidden && box.innerHTML.trim()){
        showResult();
      }
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
