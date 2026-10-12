import numpy as np, tensorflow as tf, sys, os
out=sys.argv[1]; rng=np.random.RandomState(7)
W1=rng.normal(0,0.3,(64,32)).astype('float32'); b1=rng.normal(0,0.1,32).astype('float32')
W2=rng.normal(0,0.3,(32,32)).astype('float32'); b2=rng.normal(0,0.1,32).astype('float32')
W3=rng.normal(0,0.3,(32,1)).astype('float32'); b3=np.zeros(1,'float32')
X=rng.uniform(-1,1,(256,64)).astype('float32'); np.save(f"{out}/x_float.npy", X[:4])
def dense_chain(inp):
    d=tf.keras.layers.Dense(32,activation='relu'); e=tf.keras.layers.Dense(32,activation='relu'); f=tf.keras.layers.Dense(1)
    y=f(e(d(inp))); return y,(d,e,f)
variants={}
i=tf.keras.Input((64,),batch_size=1); y,ls=dense_chain(i); variants['A_2d']=(tf.keras.Model(i,y),ls,lambda x:x)
i=tf.keras.Input((1,1,64),batch_size=1); y,ls=dense_chain(i); variants['B_4d_dense']=(tf.keras.Model(i,y),ls,lambda x:x.reshape(-1,1,1,64))
i=tf.keras.Input((1,1,64),batch_size=1); r=tf.keras.layers.Reshape((64,))(i); y,ls=dense_chain(r); variants['C_4d_reshape']=(tf.keras.Model(i,y),ls,lambda x:x.reshape(-1,1,1,64))
for name,(m,ls,shape) in variants.items():
    for l,(W,b) in zip(ls,[(W1,b1),(W2,b2),(W3,b3)]): l.set_weights([W,b])
    def rep():
        for k in range(100): yield [shape(X[k:k+1])]
    c=tf.lite.TFLiteConverter.from_keras_model(m); c.optimizations=[tf.lite.Optimize.DEFAULT]; c.representative_dataset=rep
    c.target_spec.supported_ops=[tf.lite.OpsSet.TFLITE_BUILTINS_INT8]; c.inference_input_type=tf.int8; c.inference_output_type=tf.int8
    tfl=c.convert(); open(f"{out}/{name}.tflite","wb").write(tfl)
    it=tf.lite.Interpreter(model_content=tfl); it.allocate_tensors(); di=it.get_input_details()[0]; do=it.get_output_details()[0]
    sc,zp=di['quantization']; q=np.clip(np.rint(shape(X[:4])/sc+zp),-128,127).astype(np.int8)
    outs=[]
    for k in range(4): it.set_tensor(di['index'],q[k:k+1]); it.invoke(); outs.append(int(it.get_tensor(do['index']).ravel()[0]))
    np.save(f"{out}/{name}.q.npy",q); np.save(f"{out}/{name}.tflite_out.npy",np.array(outs,dtype=np.int8))
    ops=sorted({it._get_ops_details()[k]['op_name'] for k in range(len(it._get_ops_details()))})
    print(name,"in",di['shape'].tolist(),"ops",ops,"tflite_raw",outs,"float",[round(float(v),4) for v in m.predict(shape(X[:4]),verbose=0).ravel()])
