import numpy as np, tensorflow as tf, sys
out=sys.argv[1]; rng=np.random.RandomState(7)
W1=rng.normal(0,0.3,(64,32)).astype('float32'); b1=rng.normal(0,0.1,32).astype('float32')
W2=rng.normal(0,0.3,(32,32)).astype('float32'); b2=rng.normal(0,0.1,32).astype('float32')
W3=rng.normal(0,0.3,(32,1)).astype('float32'); b3=np.zeros(1,'float32')
X=rng.uniform(-1,1,(256,64)).astype('float32')
variants={}
i=tf.keras.Input((1,1,64),batch_size=1); c1=tf.keras.layers.Conv2D(32,1,activation='relu'); c2=tf.keras.layers.Conv2D(32,1,activation='relu'); c3=tf.keras.layers.Conv2D(1,1)
y=c3(c2(c1(i))); variants['D_conv1x1']=(tf.keras.Model(i,y),[(c1,W1.reshape(1,1,64,32),b1),(c2,W2.reshape(1,1,32,32),b2),(c3,W3.reshape(1,1,32,1),b3)],lambda x:x.reshape(-1,1,1,64))
i=tf.keras.Input((64,),batch_size=1); d=tf.keras.layers.Dense(1); y=d(i); variants['E_single_dense']=(tf.keras.Model(i,y),[(d,W1[:,:1].copy(),b1[:1].copy())],lambda x:x)
i=tf.keras.Input((64,),batch_size=1); d=tf.keras.layers.Dense(32,activation='relu'); y=d(i); variants['F_dense_relu']=(tf.keras.Model(i,y),[(d,W1,b1)],lambda x:x)
for name,(m,ls,shape) in variants.items():
    for l,W,b in ls: l.set_weights([W,b])
    def rep():
        for k in range(100): yield [shape(X[k:k+1])]
    c=tf.lite.TFLiteConverter.from_keras_model(m); c.optimizations=[tf.lite.Optimize.DEFAULT]; c.representative_dataset=rep
    c.target_spec.supported_ops=[tf.lite.OpsSet.TFLITE_BUILTINS_INT8]; c.inference_input_type=tf.int8; c.inference_output_type=tf.int8
    tfl=c.convert(); open(f"{out}/{name}.tflite","wb").write(tfl)
    it=tf.lite.Interpreter(model_content=tfl); it.allocate_tensors(); di=it.get_input_details()[0]; do=it.get_output_details()[0]
    sc,zp=di['quantization']; q=np.clip(np.rint(shape(X[:4])/sc+zp),-128,127).astype(np.int8)
    outs=[]
    for k in range(4): it.set_tensor(di['index'],q[k:k+1]); it.invoke(); outs.append(it.get_tensor(do['index']).ravel().astype(int).tolist())
    np.save(f"{out}/{name}.q.npy",q); np.save(f"{out}/{name}.tflite_out.npy",np.array(outs,dtype=np.int8))
    print(name,"in",di['shape'].tolist(),"out",do['shape'].tolist(),"tflite_raw(first vals)",[o[:3] for o in outs])
